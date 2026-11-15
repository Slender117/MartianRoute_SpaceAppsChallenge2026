// Tipos para importar imágenes (import foto from "...webp"). Next los declara en next-env.d.ts,
// pero ese archivo no se versiona y no existe cuando CI corre tsc antes de next build.
/// <reference types="next/image-types/global" />
