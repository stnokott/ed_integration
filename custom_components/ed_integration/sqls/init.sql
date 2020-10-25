drop table if exists SYSTEMS;

create table SYSTEMS
(
	id integer not null
		constraint SYSTEMS_pk
			primary key,
	edsm_id integer,
	name text not null,
	x real not null,
	y real not null,
	z real not null,
	population integer not null,
	is_populated integer,
	government_id integer,
	government text,
	allegiance_id integer,
	allegiance text,
	security_id integer,
	security text,
	primary_economy_id integer,
	primary_economy text,
	power text,
	power_state text,
	power_state_id integer,
	needs_permit integer not null,
	updated_at integer,
	controlling_minor_faction_id integer,
	controlling_minor_faction text,
	reserve_type_id integer,
	reserve_type text
);

create unique index SYSTEMS_id_uindex
	on SYSTEMS (id);

create unique index SYSTEMS_name_uindex
	on SYSTEMS (name);

drop table if exists SYSTEMS_META;

create table SYSTEMS_META
(
    id integer not null
        constraint META_pk
            primary key,
    last_updated_date timestamp
);

create unique index SYSTEMS_META_id_uindex
    on SYSTEMS_META (id);

insert into SYSTEMS_META
(
    id,
    last_updated
) VALUES (
    1,
    NULL
);