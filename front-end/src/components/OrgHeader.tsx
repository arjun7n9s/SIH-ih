import { Link } from "react-router-dom";

/** Original org lockup — no background removal. */
const ORG_HEADER_SRC = "/brand/iiitdmj-org-header.png";

type Props = {
  to?: string;
  className?: string;
  compact?: boolean;
};

export function OrgHeader({ to = "/", className = "", compact = false }: Props) {
  const img = (
    <img
      src={ORG_HEADER_SRC}
      alt="PDPM IIITDM Jabalpur"
      className={`object-contain object-left ${compact ? "h-9 sm:h-10" : "h-12 sm:h-14"}`}
    />
  );

  if (to) {
    return (
      <Link to={to} className={`inline-flex items-center ${className}`} aria-label="PDPM IIITDM Jabalpur">
        {img}
      </Link>
    );
  }

  return (
    <div className={`inline-flex items-center ${className}`} aria-label="PDPM IIITDM Jabalpur">
      {img}
    </div>
  );
}
