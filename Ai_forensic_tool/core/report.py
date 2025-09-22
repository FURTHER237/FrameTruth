from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

router = APIRouter()

@router.post("/api/generate-report")
def generate_report(data: dict):
    print("Payload received:", data)
    image_path = data.get("image_path")
    mask_path = data.get("mask_path")
    confidence = data.get("confidence")
    metadata = data.get("metadata")

    if not image_path or not mask_path:
        raise HTTPException(status_code=400, detail="Image or mask path missing")


    if not image_path or not mask_path:
        raise HTTPException(status_code=400, detail="Image or mask path missing")

    styles = getSampleStyleSheet()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=A4)
    story = []

    # Add title and confidence
    story.append(Paragraph("<b>FrameTruth Forensic Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Confidence of Forgery: {confidence*100:.1f}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Add metadata
    if metadata:
        story.append(Paragraph("<b>Metadata:</b>", styles["Heading2"]))
        for k, v in metadata.items():
            story.append(Paragraph(f"{k}: {v}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # Add images
    story.append(RLImage(image_path, width=250, height=250))
    story.append(Spacer(1, 12))
    story.append(RLImage(mask_path, width=250, height=250))

    doc.build(story)

    return FileResponse(
        tmp.name,
        media_type="application/pdf",
        filename="forensic_report.pdf"
    )
