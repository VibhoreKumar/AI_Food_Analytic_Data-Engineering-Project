select
    *
from {{ source('raw', 'menu') }}
