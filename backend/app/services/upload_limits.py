"""Bounded survey uploads and archive expansion, before native parsers run."""
from pathlib import PurePosixPath
import stat
import math

SURVEY_UPLOAD_MAX_BYTES = 32 * 1024 * 1024
ARCHIVE_MAX_MEMBERS = 128
ARCHIVE_MAX_TOTAL_BYTES = 64 * 1024 * 1024
ARCHIVE_MAX_MEMBER_BYTES = 32 * 1024 * 1024
ARCHIVE_MAX_RATIO = 200
GEOJSON_MAX_NODES = 200000
GEOJSON_MAX_DEPTH = 32
GEOJSON_MAX_FEATURES = 10000


def validate_geojson_input(data):
    """Bound decoded data before geometry reprojection or database writes."""
    if not isinstance(data, dict):
        raise ValueError('GeoJSON must be an object')
    stack = [(data, 0)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > GEOJSON_MAX_NODES or depth > GEOJSON_MAX_DEPTH:
            raise ValueError('GeoJSON complexity exceeds import limits')
        if isinstance(value, dict):
            if nodes + len(stack) + len(value) > GEOJSON_MAX_NODES:
                raise ValueError('GeoJSON complexity exceeds import limits')
            stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            if nodes + len(stack) + len(value) > GEOJSON_MAX_NODES:
                raise ValueError('GeoJSON complexity exceeds import limits')
            stack.extend((v, depth + 1) for v in value)
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError('GeoJSON contains non-finite numbers')
    allowed = {'Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon', 'GeometryCollection'}
    def geometry(value):
        if not isinstance(value, dict) or value.get('type') not in allowed:
            raise ValueError('Unsupported GeoJSON geometry')
        if value['type'] == 'GeometryCollection':
            if not isinstance(value.get('geometries'), list):
                raise ValueError('Invalid GeoJSON geometry collection')
            for child in value['geometries']:
                geometry(child)
        elif not isinstance(value.get('coordinates'), list):
            raise ValueError('GeoJSON coordinates must be an array')
    def feature(value):
        if not isinstance(value, dict) or value.get('type') != 'Feature':
            raise ValueError('Invalid GeoJSON feature')
        geometry(value.get('geometry'))
    if data.get('type') == 'FeatureCollection':
        features = data.get('features')
        if not isinstance(features, list) or not features or len(features) > GEOJSON_MAX_FEATURES:
            raise ValueError('GeoJSON feature count exceeds import limits or is empty')
        for value in features:
            feature(value)
    elif data.get('type') == 'Feature':
        feature(data)
    else:
        geometry(data)
    return data


def validate_archive(archive):
    members = archive.infolist()
    if len(members) > ARCHIVE_MAX_MEMBERS:
        raise ValueError('Survey archive has too many members')
    total = 0
    names = set()
    for member in members:
        name = member.filename
        path = PurePosixPath(name)
        if (not name or '\\' in name or ':' in name or '\x00' in name
                or path.is_absolute() or '..' in path.parts or len(name) > 240
                or name.casefold() in names or stat.S_ISLNK(member.external_attr >> 16)
                or member.flag_bits & 1):
            raise ValueError('Unsafe survey archive member')
        names.add(name.casefold())
        total += member.file_size
        if (member.file_size > ARCHIVE_MAX_MEMBER_BYTES or total > ARCHIVE_MAX_TOTAL_BYTES
                or member.file_size > max(1, member.compress_size) * ARCHIVE_MAX_RATIO):
            raise ValueError('Survey archive expansion exceeds bounded limits')
    return members
