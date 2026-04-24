interface LoadingBlockProps {
  label?: string;
}

export function LoadingBlock({ label = "Loading..." }: LoadingBlockProps) {
  return <div className="loading-block">{label}</div>;
}
