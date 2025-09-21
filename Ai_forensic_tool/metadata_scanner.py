import os
import sys
import hashlib
from datetime import datetime
from PIL import Image, ExifTags
import exifread
from datetime import datetime, timezone


def sha256sum(filename, block_size=65536):
    h = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()

def format_time(epoch_time):
    return datetime.fromtimestamp(epoch_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_exif_field(exif, field_name):
    for tag, value in exif.items():
        if tag == field_name:
            return str(value)
    return None

def extract_gps(exif_tags):
    gps_lat = exif_tags.get("GPS GPSLatitude")
    gps_lat_ref = exif_tags.get("GPS GPSLatitudeRef")
    gps_lon = exif_tags.get("GPS GPSLongitude")
    gps_lon_ref = exif_tags.get("GPS GPSLongitudeRef")
    gps_alt = exif_tags.get("GPS GPSAltitude")

    def convert_to_degrees(value):
        d, m, s = [float(x.num) / float(x.den) for x in value.values]
        return d + (m / 60.0) + (s / 3600.0)

    lat, lon, alt = None, None, None
    if gps_lat and gps_lon:
        lat = convert_to_degrees(gps_lat)
        if gps_lat_ref and gps_lat_ref.values[0] == "S":
            lat = -lat
        lon = convert_to_degrees(gps_lon)
        if gps_lon_ref and gps_lon_ref.values[0] == "W":
            lon = -lon
    if gps_alt:
        alt = float(gps_alt.values[0].num) / float(gps_alt.values[0].den)

    return lat, lon, alt

def print_metadata(image_path):
    print(f"File: {os.path.basename(image_path)}")
    print(f"Size: {os.path.getsize(image_path):,} bytes")
    print(f"Hash (SHA256): {sha256sum(image_path)}")

    stat = os.stat(image_path)
    print("\n[File Timestamps]")
    print(f"Created: {format_time(stat.st_ctime)}")
    print(f"Modified: {format_time(stat.st_mtime)}")
    print(f"Accessed: {format_time(stat.st_atime)}")

    print("\n[Camera Information]")
    make, model, serial, lens, date_taken = None, None, None, None, None

    # --- Extract EXIF ---
    with open(image_path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    make = tags.get("Image Make")
    model = tags.get("Image Model")
    serial = tags.get("Image BodySerialNumber")
    lens = tags.get("EXIF LensModel")
    date_taken = tags.get("EXIF DateTimeOriginal")

    if make: print(f"Make: {make}")
    if model: print(f"Model: {model}")
    if serial: print(f"Serial Number: {serial}")
    if lens: print(f"Lens Model: {lens}")
    if date_taken: print(f"Date Taken: {date_taken}")

    print("\n[Location Data]")
    lat, lon, alt = extract_gps(tags)
    if lat and lon:
        print(f"Latitude: {lat:.6f}")
        print(f"Longitude: {lon:.6f}")
    if alt is not None:
        print(f"Altitude: {alt:.2f} m")

    print("\n[Software / Editing]")
    software = tags.get("Image Software")
    desc = tags.get("Image ImageDescription")
    copyright_ = tags.get("Image Copyright")

    if software: print(f"Software: {software}")
    if desc: print(f"Description: \"{desc}\"")
    if copyright_: print(f"Copyright: {copyright_}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_meta.py <image_file>")
    else:
        print_metadata(sys.argv[1])
