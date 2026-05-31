"""Generate the bundled, OBVIOUSLY-FICTIONAL sample PDFs with reportlab.

The generated PDFs live in sample_docs/ and are committed to the repo, so the
demo never needs reportlab at runtime — this script just documents how they
were produced and lets you regenerate them:

    pip install reportlab
    python tools/make_samples.py

Every company, name, email, phone and figure here is invented for the demo.
"""
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer)

OUT = Path(__file__).resolve().parent.parent / "sample_docs"

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=6)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.5,
                      leading=15, alignment=TA_LEFT, spaceAfter=8)
NOTE = ParagraphStyle("Note", parent=BODY, textColor="#777777", fontSize=9)


def build(filename: str, title: str, blocks: list) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT / filename), pagesize=LETTER,
                            topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                            leftMargin=1 * inch, rightMargin=1 * inch,
                            title=title)
    story = [Paragraph(title, H1),
             Paragraph("Fictional sample document.", NOTE),
             Spacer(1, 10)]
    for block in blocks:
        kind, text = block
        if kind == "page":
            story.append(PageBreak())
        elif kind == "h2":
            story.append(Paragraph(text, H2))
        else:
            story.append(Paragraph(text, BODY))
    doc.build(story)
    print("wrote", filename)


def handbook() -> None:
    build(
        "acme_employee_handbook.pdf",
        "Acme Corporation — Employee Handbook",
        [
            ("h2", "1. Working Hours"),
            ("p", "Standard working hours at Acme Corporation are 9:00 AM to 5:00 PM, "
                  "Monday through Friday. Core collaboration hours, when all employees "
                  "are expected to be reachable, are 10:00 AM to 3:00 PM."),
            ("h2", "2. Remote Work Policy"),
            ("p", "Employees may work remotely up to three days per week. Requests for "
                  "fully-remote arrangements must be approved by your manager and the "
                  "People team. Acme reimburses up to $200 per year for home-office "
                  "equipment; submit receipts through the Acme expense portal."),
            ("page", ""),
            ("h2", "3. Paid Time Off"),
            ("p", "Full-time employees accrue 20 days of paid vacation per year, accrued "
                  "monthly. Up to 5 unused vacation days may be carried over into the "
                  "following year. In addition, employees receive 10 paid sick days "
                  "annually, which do not carry over."),
            ("h2", "4. Parental Leave"),
            ("p", "Acme offers 16 weeks of fully-paid parental leave to all new parents, "
                  "available within the first 12 months of a child's arrival."),
            ("page", ""),
            ("h2", "5. Expense Reimbursement"),
            ("p", "Business expenses must be submitted within 30 days of the purchase "
                  "date through the expense portal. Approved expenses are reimbursed in "
                  "the next payroll cycle. Expenses over $500 require pre-approval from "
                  "your manager."),
            ("h2", "6. Code of Conduct"),
            ("p", "All employees are expected to treat colleagues with respect. "
                  "Questions about this handbook can be directed to the People team at "
                  "people@example.com or extension 555-0142."),
        ],
    )


def manual() -> None:
    build(
        "globex_widget3000_manual.pdf",
        "Globex Widget 3000 — Product Manual",
        [
            ("h2", "Overview"),
            ("p", "Thank you for choosing the Globex Widget 3000, a fictional device "
                  "used here as sample documentation. This manual covers setup, features, "
                  "troubleshooting and warranty."),
            ("h2", "Getting Started"),
            ("p", "1. Remove the Widget 3000 from its packaging. 2. Charge the device "
                  "fully before first use using the included USB-C cable. 3. Press and "
                  "hold the power button for 3 seconds to turn it on. 4. Follow the "
                  "on-device prompts to pair with the Globex companion app."),
            ("page", ""),
            ("h2", "Battery & Charging"),
            ("p", "The Widget 3000 has a battery life of approximately 8 hours of "
                  "continuous use. A full charge takes about 90 minutes. The battery "
                  "indicator turns amber when below 20% and green when fully charged."),
            ("h2", "Key Features"),
            ("p", "The Widget 3000 is water-resistant to IPX5, supports Bluetooth 5.2, "
                  "and includes three brightness modes. The device weighs 180 grams."),
            ("page", ""),
            ("h2", "Troubleshooting"),
            ("p", "If the Widget 3000 becomes unresponsive, perform a hard reset by "
                  "holding the power button for 10 seconds until the indicator blinks "
                  "red. If pairing fails, ensure Bluetooth is enabled and the device is "
                  "within 5 metres. For persistent issues, contact Globex support at "
                  "support@example.com or 1-555-0177."),
            ("h2", "Warranty"),
            ("p", "The Widget 3000 includes a 12-month limited warranty covering "
                  "manufacturing defects. The warranty does not cover accidental damage "
                  "or water damage beyond the IPX5 rating."),
        ],
    )


def refund_policy() -> None:
    build(
        "initech_refund_policy.pdf",
        "Initech Online Store — Refund & Returns Policy",
        [
            ("h2", "1. Refund Window"),
            ("p", "Initech accepts returns within 30 days of the delivery date. To be "
                  "eligible for a refund, items must be unused and in their original "
                  "packaging. Proof of purchase is required."),
            ("h2", "2. How to Request a Refund"),
            ("p", "To start a return, email refunds@example.com with your order number, "
                  "or call our support line at 1-555-0100 (Mon–Fri, 9 AM–5 PM). You will "
                  "receive a prepaid return label within two business days."),
            ("page", ""),
            ("h2", "3. Processing Time"),
            ("p", "Once we receive your returned item, refunds are processed within 5 to "
                  "7 business days to the original payment method. You will receive an "
                  "email confirmation when your refund has been issued."),
            ("h2", "4. Non-Refundable Items"),
            ("p", "Gift cards, downloadable software, and personalised items are "
                  "non-refundable. Shipping charges are non-refundable unless the return "
                  "is due to an Initech error."),
            ("page", ""),
            ("h2", "5. Exchanges"),
            ("p", "If you received a defective or damaged item, Initech will exchange it "
                  "at no cost. Contact refunds@example.com within 30 days of delivery to "
                  "arrange an exchange."),
            ("h2", "6. Contact"),
            ("p", "For any questions about this fictional policy, contact the Initech "
                  "support team at refunds@example.com or 1-555-0100."),
        ],
    )


if __name__ == "__main__":
    handbook()
    manual()
    refund_policy()
    print("done →", OUT)
