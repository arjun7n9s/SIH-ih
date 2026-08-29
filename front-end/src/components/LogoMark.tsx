type Props = {
  size?: number;
  className?: string;
};

export function LogoMark({ size = 72, className = "" }: Props) {
  return (
    <div
      className={`relative grid place-items-center rounded-full bg-gradient-to-br from-green-soft to-blue-soft shadow-[0_18px_50px_-28px_rgba(11,122,59,0.55)] ring-1 ring-line ${className}`}
      style={{ width: size, height: size }}
    >
      <img
        src="/iiitdmj-logo.png"
        alt="IIITDM Jabalpur"
        width={Math.round(size * 0.62)}
        height={Math.round(size * 0.62)}
        className="object-contain"
      />
    </div>
  );
}
