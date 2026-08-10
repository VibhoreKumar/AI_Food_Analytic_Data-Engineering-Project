select
    *
from {{ source('raw', 'restaurants') }}
