{{ config(
    unique_key = '_airbyte_ab_id',
    schema = "_airbyte_test_normalization",
    tags = [ "top-level-intermediate" ]
) }}
-- SQL model to cast each column to its adequate SQL type converted from the JSON schema type
-- depends_on: {{ ref('renamed_dedup_cdc_excluded_ab1') }}
select
    accurateCastOrNull(trim(BOTH '"' from id), '{{ dbt_utils.type_bigint() }}') as id,
    accurateCastOrNull(trim(BOTH '"' from _ab_cdc_updated_at), '{{ dbt_utils.type_float() }}') as _ab_cdc_updated_at,
    _airbyte_ab_id,
    _airbyte_emitted_at,
    {{ current_timestamp() }} as _airbyte_normalized_at
from {{ ref('renamed_dedup_cdc_excluded_ab1') }}
-- renamed_dedup_cdc_excluded
where 1 = 1
{{ incremental_clause('_airbyte_emitted_at', this) }}

