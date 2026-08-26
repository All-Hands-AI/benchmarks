Add QoL improvements for deserializing geometry
While the changes in #296 don't add much generic friction in most places, decoding geometry is one notable exception. Currently you must specialize the generic geometry type explicitly in the function call e.g. `Geometry<XY>(wkb: ...)` or  `decoder.decode(Geometry<XY>.self)`. It would be nice to have a more ergonomic API or even provide a wrapper that can handle multiple different coordinate types if you don't know what a source is going to give you.

Relevant interfaces:
Method: CodingUserInfoKey.geoJSONSetMissingZNan (static let) 
Location: Sources/GEOSwift/Codable/CodableGeometry.swift 
Inputs: None (static property). Used via `decoder.userInfo[.geoJSONSetMissingZNan]` where the value should be a `Bool`. If set to `true`, missing Z coordinates in GeoJSON are decoded as `Double.nan`; if absent, `false`, or any non‑Bool value, the default behavior (throwing `GEOSwiftError.invalidCoordinates`) applies. 
Outputs: Returns a `CodingUserInfoKey` instance with raw value `"GEOSwift.geoJSONSetMissingZNan"`. This key enables the decoding logic in `XYZ.init(from:)` to decide how to handle absent Z values. 
Description: A user‑info key for JSON decoders that toggles whether XYZ decoding tolerates missing Z values by substituting `nan` instead of raising an error. Use it when decoding `Geometry<XYZ>` from GeoJSON with unknown dimensionality.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

