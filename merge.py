"""
Merge the 12 Wokelo OpenAPI source YAMLs into one unified spec.

Strategy:
- Unify info/servers/security/tags at the top
- For path collisions (same path + method from multiple sources):
    build a single merged operation with a oneOf requestBody/response
- Deduplicate schemas:
    - if content identical across files: keep once (silent)
    - if content differs: rename later copies with a short tag-prefix
- Preserve every example, description, and schema faithfully
"""
import yaml
import json
from pathlib import Path
from collections import OrderedDict, defaultdict

SOURCES_DIR = Path('sources')

# --- Custom YAML dumper for stable, readable output ---
class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter, Dumper=IndentDumper)
# Preserve dict order
yaml.add_representer(
    dict,
    lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()),
    Dumper=IndentDumper,
)
yaml.add_representer(
    OrderedDict,
    lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()),
    Dumper=IndentDumper,
)

# --- Load every source file ---
sources = {}
for src in sorted(SOURCES_DIR.glob('wokelo_*.yaml')):
    with open(src) as f:
        sources[src.stem] = yaml.safe_load(f)

# --- Short tag prefix per source (for renamed schemas) ---
SHORT_TAG = {
    'wokelo_buyer_screening_openapi':          'Buyer',
    'wokelo_company_deep_intelligence_openapi':'CompanyDeep',
    'wokelo_company_instant_enrichment_openapi':'CompanyInstant',
    'wokelo_company_news_monitoring_openapi':  'News',
    'wokelo_company_research_openapi':         'CompanyResearch',
    'wokelo_custom_workflows_openapi':         'CustomWF',
    'wokelo_industry_deep_intelligence_openapi':'IndustryDeep',
    'wokelo_industry_research_openapi':        'IndustryResearch',
    'wokelo_market_map_openapi':               'MarketMap',
    'wokelo_peer_comparison_openapi':          'Peer',
    'wokelo_supporting_apis_openapi':          'Support',
    'wokelo_target_screening_openapi':         'Target',
}

# --- Phase 1: collect schemas with dedup/rename ---
final_schemas = OrderedDict()
schema_rename_map = {}  # (source, original_name) -> final_name

def canonical(obj):
    """Deterministic JSON representation for content comparison."""
    return json.dumps(obj, sort_keys=True, default=str)

# First pass: group schemas by name to detect duplicates
name_to_sources = defaultdict(list)
for source_name, spec in sources.items():
    schemas = (spec.get('components') or {}).get('schemas') or {}
    for schema_name, schema_def in schemas.items():
        name_to_sources[schema_name].append((source_name, schema_def))

# Second pass: decide final name for each (source, schema_name) pair
for schema_name, occurrences in name_to_sources.items():
    if len(occurrences) == 1:
        source_name, schema_def = occurrences[0]
        final_schemas[schema_name] = schema_def
        schema_rename_map[(source_name, schema_name)] = schema_name
        continue

    # Multiple sources define this schema. Compare content.
    canonicals = [(src, canonical(defn), defn) for src, defn in occurrences]
    first_canon = canonicals[0][1]
    all_identical = all(c[1] == first_canon for c in canonicals)

    if all_identical:
        # Silent dedup - use one copy
        final_schemas[schema_name] = occurrences[0][1]
        for src, _ in occurrences:
            schema_rename_map[(src, schema_name)] = schema_name
    else:
        # Content differs - keep first unqualified, rename others
        first_src, first_def = occurrences[0]
        final_schemas[schema_name] = first_def
        schema_rename_map[(first_src, schema_name)] = schema_name
        for src, defn in occurrences[1:]:
            new_name = f"{SHORT_TAG[src]}{schema_name}"
            final_schemas[new_name] = defn
            schema_rename_map[(src, schema_name)] = new_name

# --- Phase 2: rewrite $refs in every collected schema ---
def rewrite_refs(obj, source_name):
    """Recursively rewrite $ref strings using the rename map for the given source."""
    if isinstance(obj, dict):
        if '$ref' in obj and obj['$ref'].startswith('#/components/schemas/'):
            old_name = obj['$ref'].split('/')[-1]
            new_name = schema_rename_map.get((source_name, old_name), old_name)
            obj['$ref'] = f'#/components/schemas/{new_name}'
        for v in obj.values():
            rewrite_refs(v, source_name)
    elif isinstance(obj, list):
        for item in obj:
            rewrite_refs(item, source_name)

# Rewrite refs inside final_schemas using each schema's original source
# Build name -> source mapping from occurrences
for schema_name, occurrences in name_to_sources.items():
    for source_name, _ in occurrences:
        final_name = schema_rename_map[(source_name, schema_name)]
        if final_name in final_schemas:
            # The rewriting might double-process when deduped-identical;
            # that's OK since it's idempotent.
            rewrite_refs(final_schemas[final_name], source_name)

# --- Phase 3: collect paths, handling collisions ---
path_operations = defaultdict(dict)  # path -> {method: [(source, operation)]}
for source_name, spec in sources.items():
    for path, ops in (spec.get('paths') or {}).items():
        for method, op in ops.items():
            if method not in ('get', 'post', 'put', 'delete', 'patch'):
                continue
            # Rewrite refs inside the operation using this source's mapping
            rewrite_refs(op, source_name)
            path_operations[path].setdefault(method, []).append((source_name, op))

def merge_operations(ops_list, path, method):
    """Merge multiple operations at the same path+method into one.

    Produces: single operation with oneOf requestBody and oneOf 200 response,
    preserving all descriptions/examples.
    """
    # Use tags from all sources, unique
    all_tags = []
    for _, op in ops_list:
        for t in op.get('tags', []):
            if t not in all_tags:
                all_tags.append(t)

    # Unique operationId: combine (or pick the first - and add others as alternates)
    primary = ops_list[0][1]
    op_ids = [op.get('operationId', f'op_{i}') for i, (_, op) in enumerate(ops_list)]
    combined_op_id = primary.get('operationId') or f"dispatch_{path.replace('/', '_').strip('_')}"

    # Summary/description: show that multiple modes are supported
    summaries = [op.get('summary', '') for _, op in ops_list]
    descriptions = [op.get('description', '') for _, op in ops_list]

    merged_description = (
        "This endpoint dispatches to multiple behaviors based on the request body.\n\n"
        + "\n\n---\n\n".join(
            f"**Mode: {tag_for_op(op)}**\n\n{op.get('description', '').strip()}"
            for _, op in ops_list
        )
    )

    # Build oneOf request body
    request_schemas = []
    request_examples = {}
    for src, op in ops_list:
        rb = op.get('requestBody', {})
        content = rb.get('content', {}).get('application/json', {})
        schema = content.get('schema')
        example = content.get('example')
        if schema:
            request_schemas.append(schema)
        if example is not None:
            request_examples[tag_for_op(op)] = {'summary': tag_for_op(op), 'value': example}

    merged_request_body = {
        'required': True,
        'content': {
            'application/json': {
                'schema': {'oneOf': request_schemas} if len(request_schemas) > 1 else (request_schemas[0] if request_schemas else {}),
            }
        }
    }
    if request_examples:
        merged_request_body['content']['application/json']['examples'] = request_examples

    # Build oneOf 200 response
    success_schemas = []
    success_examples = {}
    shared_error_responses = OrderedDict()
    for src, op in ops_list:
        responses = op.get('responses', {})
        for code, resp_def in responses.items():
            if code == '200':
                content = resp_def.get('content', {}).get('application/json', {})
                s = content.get('schema')
                e = content.get('example')
                if s:
                    success_schemas.append(s)
                if e is not None:
                    success_examples[tag_for_op(op)] = {'summary': tag_for_op(op), 'value': e}
            else:
                # Shared error responses - first wins
                if code not in shared_error_responses:
                    shared_error_responses[code] = resp_def

    merged_200 = {
        'description': 'Dispatched operation completed successfully.',
        'content': {
            'application/json': {
                'schema': {'oneOf': success_schemas} if len(success_schemas) > 1 else (success_schemas[0] if success_schemas else {}),
            }
        }
    }
    if success_examples:
        merged_200['content']['application/json']['examples'] = success_examples

    merged_responses = OrderedDict()
    merged_responses['200'] = merged_200
    for code, resp in shared_error_responses.items():
        merged_responses[code] = resp

    merged_op = OrderedDict()
    merged_op['tags'] = all_tags
    merged_op['operationId'] = combined_op_id
    merged_op['summary'] = " / ".join(summaries)
    merged_op['description'] = merged_description
    merged_op['requestBody'] = merged_request_body
    merged_op['responses'] = merged_responses
    return merged_op

def tag_for_op(op):
    tags = op.get('tags', [])
    return tags[0] if tags else op.get('operationId', 'unknown')

# Need to re-run collision processing now that helpers are defined
final_paths = OrderedDict()
collision_notes = []
for path in sorted(path_operations.keys()):
    methods = path_operations[path]
    final_paths[path] = OrderedDict()
    for method in sorted(methods.keys()):
        ops = methods[method]
        if len(ops) == 1:
            final_paths[path][method] = ops[0][1]
        else:
            collision_notes.append((path, method, [s for s, _ in ops]))
            final_paths[path][method] = merge_operations(ops, path, method)

# --- Phase 4: build unified tags list (one per original API) ---
unified_tags = [
    {'name': 'Company Instant Enrichment', 'description': 'Instant fundamentals and alternative data on cached companies (20M+).'},
    {'name': 'Company Deep Intelligence',  'description': 'On-demand deep intelligence with custom parameters on any company.'},
    {'name': 'Industry Deep Intelligence', 'description': 'On-demand intelligence with custom parameters on any industry.'},
    {'name': 'Market Map',                 'description': 'Ranked company discovery within a market category.'},
    {'name': 'Target Screening',           'description': 'Scored acquisition targets for a defined acquirer.'},
    {'name': 'Buyer Screening',            'description': 'Scored buyers for a defined target company.'},
    {'name': 'Company News Monitoring',    'description': 'News retrieval, enrichment, and filtering for a specific company.'},
    {'name': 'Company Research',           'description': 'End-to-end company research report.'},
    {'name': 'Industry Research',          'description': 'End-to-end sector coverage report.'},
    {'name': 'Peer Comparison',            'description': 'Multi-company comparative analysis across chosen dimensions.'},
    {'name': 'Custom Workflows',           'description': 'Trigger custom research workflows built in Wokelo.'},
    {'name': 'Company Search',             'description': 'Search and resolve company identifiers.'},
    {'name': 'File Upload',                'description': 'Upload assets used by other workflows.'},
    {'name': 'Request Lifecycle',          'description': 'Check status, cancel, or fetch results of async requests.'},
    {'name': 'Report Lifecycle',           'description': 'Check status of and download generated reports.'},
    {'name': 'Report Configuration',       'description': 'Configure and retrieve report metadata.'},
]

# --- Phase 5: assemble final spec ---
final_spec = OrderedDict()
final_spec['openapi'] = '3.1.0'
final_spec['info'] = {
    'title': 'Wokelo API',
    'version': '1.0.0',
    'summary': 'Purpose-built API suite for dealmaking AI infrastructure.',
    'description': (
        "Wokelo's API suite is purpose-built for developers building dealmaking AI infrastructure. "
        "It delivers structured, processed intelligence at the quality standard investment and advisory "
        "workflows demand.\n\n"
        "- Entities resolved across a proprietary database of 20M+ public and private companies.\n"
        "- News signals deduplicated across 1,000+ curated sources.\n"
        "- Every output is agent-native, source-traced, and ready to plug directly into your models, "
        "agents, and workflows without additional processing."
    ),
    'contact': {
        'name': 'Wokelo',
        'url': 'https://wokelo.ai',
        'email': 'support@wokelo.ai',
    },
    'license': {
        'name': 'Proprietary',
        'url': 'https://wokelo.ai/terms',
    },
}
final_spec['servers'] = [
    {'url': 'https://api.wokelo.ai', 'description': 'Production'},
]
final_spec['security'] = [{'bearerAuth': []}]
final_spec['tags'] = unified_tags
final_spec['paths'] = final_paths
final_spec['components'] = {
    'securitySchemes': {
        'bearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Bearer token sent in the Authorization header.',
        }
    },
    'schemas': final_schemas,
}

# Report
print("\n" + "=" * 70)
print("MERGE REPORT")
print("=" * 70)
print(f"Source files:       {len(sources)}")
print(f"Unique paths:       {len(final_paths)}")
total_ops = sum(len(ops) for ops in final_paths.values())
print(f"Total operations:   {total_ops}")
print(f"Path collisions merged: {len(collision_notes)}")
for path, method, srcs in collision_notes:
    print(f"   {method.upper()} {path}")
    for s in srcs:
        print(f"      + {s}")
print(f"Schemas in output:  {len(final_schemas)}")

# Write
with open('openapi.yaml', 'w') as f:
    yaml.dump(final_spec, f, Dumper=IndentDumper, sort_keys=False, width=120, allow_unicode=True)

print(f"\n✓ Wrote openapi.yaml ({Path('openapi.yaml').stat().st_size // 1024} KB)")
