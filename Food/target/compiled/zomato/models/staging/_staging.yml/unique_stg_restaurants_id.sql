
    
    

select
    id as unique_field,
    count(*) as n_records

from ZOMATO.staging.stg_restaurants
where id is not null
group by id
having count(*) > 1


