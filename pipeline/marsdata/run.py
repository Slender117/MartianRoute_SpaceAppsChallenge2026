"""CLI del pipeline.

marsdata synthetic [--region jezero]   región de prueba, sin descargas
marsdata fetch --region jezero         descarga datos crudos de NASA
marsdata build --region jezero         procesa crudos → data/regions/jezero
marsdata publish                       sube data/regions/ a R2

--out cambia la carpeta de salida de synthetic y build. Ojo: build escribe la región real con el
mismo ID que la sintética, y las pruebas de la API (test_demo_scenario) esperan la sintética en
data/regions; para probar la real sin pisarla, usar otra carpeta y apuntar ASSETS_DIR a ella.
"""

import argparse
from pathlib import Path

from marsdata.export import OUT_DIR, write_region
from marsdata.region import load_regions


def _build(region, out_dir: Path) -> Path:
    from marsdata.process.build import build_region
    from marsdata.process.traverse import build_traverse

    result = build_region(region)
    traverses, props = {}, {}
    for rover in region.traverse_files:
        built = build_traverse(region, result.grids["dem"], rover)
        if built:
            traverses[rover], props[rover] = built
    out = write_region(
        region,
        result.grids,
        traverses,
        out_dir=out_dir,
        layer_meta=result.layer_meta,
        traverse_properties=props,
    )
    for name, meta in result.layer_meta.items():
        print(f"{name:<20} cobertura {100 * meta['coverage']:5.1f} %")
    for rover, p in props.items():
        print(
            f"recorrido {rover}: sols {p['sol_min']} a {p['sol_max']}, "
            f"{p['length_m'] / 1000:.2f} km, {len(traverses[rover])} puntos"
        )
    for key in result.missing:
        print(f"{key:<20} sin archivo en data/raw/{region.id}: capa omitida")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(prog="marsdata")
    parser.add_argument("command", choices=["synthetic", "fetch", "build", "publish"])
    parser.add_argument("--region", default="jezero")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="carpeta de salida")
    args = parser.parse_args()

    if args.command == "publish":
        from marsdata.publish import publish

        print(f"Subidos {publish()} archivos a R2")
        return

    region = load_regions()[args.region]

    if args.command == "synthetic":
        from marsdata.synthetic import make_grids, make_traverse

        traverses = {rover: make_traverse(region) for rover in region.traverses}
        out = write_region(region, make_grids(region), traverses, out_dir=args.out, synthetic=True)
    elif args.command == "fetch":
        from marsdata.fetch.sources import fetch_region

        for key, status in fetch_region(region).items():
            print(f"{key:<16} {status}  ({region.sources[key]})")
        return
    else:
        out = _build(region, args.out)

    print(f"Región '{region.id}' escrita en {out}")


if __name__ == "__main__":
    main()
