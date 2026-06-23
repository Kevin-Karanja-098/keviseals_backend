# accounts/services.py

import random
from io import BytesIO

from django.core.files.base import ContentFile

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

def generate_otp():
    return str(random.randint(100000, 999999))


def generate_landlord_contract_pdf(contract):

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    landlord = contract.landlord

    story = []

    story.append(
        Paragraph(
            "LEVISEALS VENTURES LANDLORD AGREEMENT",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            f"Landlord: {landlord.user.email}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"National ID: {landlord.national_id}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "This agreement authorizes the landlord to use the Leviseals Property Management Platform.",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Terms and Conditions...",
            styles["Normal"]
        )
    )

    doc.build(story)

    pdf = buffer.getvalue()

    contract.generated_contract.save(
        f"contract_{contract.id}.pdf",
        ContentFile(pdf)
    )

    return contract