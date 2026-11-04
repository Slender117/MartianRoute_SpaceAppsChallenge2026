"""CLI del pipeline.

marsdata synthetic [--region jezero]   región de prueba, sin descargas
marsdata fetch --region jezero         descarga datos crudos de NASA
marsdata build --region jezero         procesa crudos → data/regions/jezero
marsdata publish                       sube data/regions/ a R2
"""

import argparse

from marsdata.export import write_region
from marsdata.region import load_regions


def main() -> None:
    parser = argparse.ArgumentParser(prog="marsdata")
    parser.add_argument("command", choices=["synthetic", "fetch", "build", "publish"])
    parser.add_argument("--region", default="jezero")
    args = parser.parse_args()

    if args.command == "publish":
        from marsdata.publish import publish

        print(f"Subidos {publish()} archivos a R2")
        return

    region = load_regions()[args.region]

    if args.command == "synthetic":
        from marsdata.synthetic import make_grids, make_traverse

        traverses = {rover: make_traverse(region) for rover in region.traverses}
        out = write_region(region, make_grids(region), traverses, synthetic=True)
    elif args.command == "fetch":
        from marsdata.fetch.sources import fetch_region

        fetch_region(region)
        return
    else:
        from marsdata.process.build import build_region

        # TODO(datos): convertir los recorridos reales de los rovers a (lat, lon).
        out = write_region(region, build_region(region))

    print(f"Región '{region.id}' escrita en {out}")


if __name__ == "__main__":
    main()
