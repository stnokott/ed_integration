INSERT OR REPLACE INTO SYSTEMS (id, edsm_id, name, x, y, z, population, is_populated, government_id, government, allegiance_id,
                     allegiance, security_id, security, primary_economy_id, primary_economy, power, power_state,
                     power_state_id, needs_permit, updated_at, controlling_minor_faction_id, controlling_minor_faction,
                     reserve_type_id, reserve_type)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
