"""Apply synthetic-only ecological eligibility rules to attributed overlaps."""

from .models import EcologyEvidenceKind, EcologyOverlap, EcologyStatus, SiteAssessment


def assess_ecology(site_id: str, overlaps: tuple[EcologyOverlap, ...]) -> SiteAssessment:
    """Apply demo-only eligibility policy; absent intersections never prove site safety."""
    if not site_id:
        raise ValueError("Site ID must not be empty")
    ordered = tuple(sorted(overlaps, key=lambda item: (item.evidence_id, item.rule_id, item.kind)))
    if any(item.kind is EcologyEvidenceKind.DEMO_RESTRICTION for item in ordered):
        status = EcologyStatus.EXCLUDED
        reasons = ("An explicit fictional exclusion geometry intersects this site",)
    elif any(item.kind is EcologyEvidenceKind.DEMO_PRECAUTION for item in ordered):
        status = EcologyStatus.CAUTION
        reasons = ("A fictional precautionary geometry intersects this site",)
    else:
        status = EcologyStatus.UNKNOWN
        reasons = ("No explicit fictional ecology zone intersects this site",)
    return SiteAssessment(
        site_id=site_id,
        status=status,
        evidence_ids=tuple(dict.fromkeys(item.evidence_id for item in ordered)),
        rule_ids=tuple(dict.fromkeys(item.rule_id for item in ordered)),
        reasons=reasons,
        unknowns=("Complete ecological coverage and legal restrictions are not verified",),
    )
