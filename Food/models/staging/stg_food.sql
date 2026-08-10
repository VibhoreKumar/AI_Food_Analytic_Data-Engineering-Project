select
    *
from {{ source('raw', 'food') }}
