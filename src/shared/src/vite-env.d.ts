// Minimal ImportMetaEnv declaration for shared code that uses import.meta.env.
// Vite provides its own types in consuming apps; this keeps shared buildable.
interface ImportMetaEnv {
  readonly DEV?: boolean;
  readonly PROD?: boolean;
  readonly MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
