#!/usr/bin/env python3
"""Generate the Rivian R2 Media Brief/RFP as a professional PDF.

This script creates a comprehensive media buying brief in classic agency RFP format
for the Rivian R2 integrated marketing campaign.

Usage:
    python rivian_r2_media_brief.py

Output:
    rivian_r2_media_brief.pdf
"""

from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib import colors

# Brand colors
RIVIAN_GREEN = HexColor('#2A6049')
RIVIAN_DARK = HexColor('#1A1A1A')
RIVIAN_GRAY = HexColor('#666666')

def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=RIVIAN_GREEN,
        spaceAfter=12,
        alignment=1  # Center
    ))

    styles.add(ParagraphStyle(
        name='DocSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=RIVIAN_GRAY,
        spaceAfter=24,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=RIVIAN_GREEN,
        spaceBefore=18,
        spaceAfter=10,
        borderPadding=5,
    ))

    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=RIVIAN_DARK,
        spaceBefore=12,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name='RivianBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=RIVIAN_DARK,
        spaceAfter=8,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=RIVIAN_DARK,
        leftIndent=20,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        alignment=1,
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontSize=9,
        textColor=RIVIAN_DARK,
    ))

    styles.add(ParagraphStyle(
        name='FooterNote',
        parent=styles['Normal'],
        fontSize=8,
        textColor=RIVIAN_GRAY,
        alignment=1,
    ))

    return styles


def build_document():
    """Build the complete RFP document."""
    doc = SimpleDocTemplate(
        "rivian_r2_media_brief.pdf",
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = create_styles()
    story = []

    # Title Page
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("MEDIA BUYING BRIEF", styles['DocTitle']))
    story.append(Paragraph("REQUEST FOR PROPOSAL", styles['DocSubtitle']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<b>RIVIAN R2 LAUNCH CAMPAIGN</b>", styles['DocTitle']))
    story.append(Paragraph("Q1-Q2 2026 Integrated Marketing Campaign", styles['DocSubtitle']))
    story.append(Spacer(1, 1*inch))

    # Document info table
    info_data = [
        ['Client:', 'Rivian Automotive, LLC'],
        ['Agency:', 'Horizon Media (Agency of Record)'],
        ['Campaign:', 'Rivian R2 Model Year Launch'],
        ['RFP Issue Date:', date.today().strftime('%B %d, %Y')],
        ['Response Due:', 'February 15, 2026'],
        ['Campaign Period:', 'March 1 - June 30, 2026'],
        ['Document Version:', '1.0 - FINAL'],
    ]

    info_table = Table(info_data, colWidths=[1.5*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), RIVIAN_DARK),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)

    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("CONFIDENTIAL - FOR AUTHORIZED RECIPIENTS ONLY", styles['FooterNote']))
    story.append(PageBreak())

    # Executive Summary
    story.append(Paragraph("1. EXECUTIVE SUMMARY", styles['SectionHeader']))
    story.append(Paragraph(
        "Rivian Automotive is launching the highly anticipated R2 - our next-generation "
        "all-electric SUV designed to bring adventure-ready capability to a broader audience. "
        "This RFP seeks qualified media partners to execute an integrated marketing campaign "
        "spanning Connected TV (CTV), Performance Digital, and Mobile App channels.",
        styles['RivianBody']
    ))
    story.append(Paragraph(
        "The campaign will drive brand awareness for the R2 launch while generating qualified "
        "leads through information requests and deposit reservations. Additionally, we aim to "
        "drive downloads and engagement of the Rivian mobile app among prospective and current customers.",
        styles['RivianBody']
    ))
    story.append(Spacer(1, 12))

    # Total Budget Summary
    budget_summary = [
        ['Campaign Component', 'Monthly Budget', '4-Month Total', 'Primary KPI'],
        ['CTV Brand Awareness', '$875,000', '$3,500,000', 'Reach & Frequency'],
        ['Performance (Web/Display)', '$200,000', '$800,000', 'Conversions'],
        ['Mobile App Install', '$100,000', '$400,000', 'Installs & Engagement'],
        ['TOTAL', '$1,175,000', '$4,700,000', '-'],
    ]

    budget_table = Table(budget_summary, colWidths=[2.2*inch, 1.3*inch, 1.3*inch, 1.8*inch])
    budget_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#E8F0EC')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(budget_table)
    story.append(PageBreak())

    # Campaign Objectives
    story.append(Paragraph("2. CAMPAIGN OBJECTIVES", styles['SectionHeader']))

    story.append(Paragraph("2.1 Primary Objectives", styles['SubSection']))
    objectives = [
        "<b>Brand Awareness:</b> Achieve 5 million unique reach with 3x weekly frequency among target audience during campaign flight",
        "<b>Lead Generation:</b> Drive qualified conversions (information requests and $100 deposit reservations) at optimal cost-per-acquisition",
        "<b>App Engagement:</b> Increase Rivian mobile app installs and drive deep-link engagement to R2 content"
    ]
    for obj in objectives:
        story.append(Paragraph(f"\u2022 {obj}", styles['BulletText']))

    story.append(Paragraph("2.2 Key Performance Indicators", styles['SubSection']))
    kpi_data = [
        ['Channel', 'Primary KPI', 'Target', 'Secondary KPIs'],
        ['CTV', 'Unique Reach', '5,000,000', 'Frequency 3x/week, VCR >90%'],
        ['Performance', 'Conversions', 'Maximize within budget', 'CPA, ROAS, CTR'],
        ['Mobile App', 'Installs', 'Maximize within budget', 'CPI, Post-Install Events'],
    ]

    kpi_table = Table(kpi_data, colWidths=[1.2*inch, 1.4*inch, 1.5*inch, 2.5*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(PageBreak())

    # Target Audience
    story.append(Paragraph("3. TARGET AUDIENCE", styles['SectionHeader']))

    story.append(Paragraph("3.1 Core Audience Profile", styles['SubSection']))
    story.append(Paragraph(
        "The Rivian R2 targets environmentally-conscious, adventure-seeking consumers who value "
        "innovation, sustainability, and premium experiences. Our ideal customer represents the "
        "next wave of EV adopters - beyond early adopters but still forward-thinking.",
        styles['RivianBody']
    ))

    audience_data = [
        ['Attribute', 'Primary Audience', 'Secondary Audience'],
        ['Age', '30-54', '25-65'],
        ['HHI', '$125,000+', '$100,000+'],
        ['Education', 'College+', 'Some College+'],
        ['Home Ownership', 'Homeowners preferred', 'All'],
        ['Geography', 'Tier 1 & 2 DMAs', 'National'],
    ]

    audience_table = Table(audience_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
    audience_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(audience_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("3.2 Psychographic & Behavioral Targeting", styles['SubSection']))
    psycho_items = [
        "<b>Interests:</b> Outdoor recreation, camping, hiking, skiing, sustainable living, technology, electric vehicles, adventure travel",
        "<b>In-Market:</b> New vehicle intenders, electric vehicle shoppers, luxury SUV/crossover considerers, automotive research",
        "<b>Life Events:</b> New home buyers, growing families, lifestyle upgraders",
        "<b>Behaviors:</b> Premium streaming subscribers, smart home device owners, eco-conscious purchase history",
        "<b>Competitive Conquest:</b> Tesla Model Y, Ford Mustang Mach-E, BMW iX, Mercedes EQS SUV, Volvo EX90 owners/intenders"
    ]
    for item in psycho_items:
        story.append(Paragraph(f"\u2022 {item}", styles['BulletText']))

    story.append(Paragraph("3.3 Hypothetical Customer Profile: \"Adventure Alex\"", styles['SubSection']))
    story.append(Paragraph(
        "<b>Alex Chen, 38, Denver, CO</b> - A product manager at a tech company earning $175,000/year. "
        "Alex and their partner own a home in a suburb with easy access to hiking trails and ski resorts. "
        "They currently drive a Tesla Model Y but are looking for more rugged capability for their outdoor adventures. "
        "Alex is an avid camper, skier, and mountain biker who values sustainability and wants a vehicle that "
        "can handle dirt roads, tow their camping trailer, and still serve as a comfortable daily driver. "
        "They stream content on HBO Max and Peacock, use Strava and AllTrails apps, and research purchases "
        "extensively online before visiting dealerships. Alex has already signed up for Rivian news updates "
        "and is comparing the R2 to the Ford F-150 Lightning and the upcoming Scout vehicles.",
        styles['RivianBody']
    ))
    story.append(PageBreak())

    # CTV Campaign Details
    story.append(Paragraph("4. CTV BRAND AWARENESS CAMPAIGN", styles['SectionHeader']))

    story.append(Paragraph("4.1 Campaign Overview", styles['SubSection']))
    ctv_overview = [
        ['Parameter', 'Specification'],
        ['Objective', 'Brand Awareness - Reach & Frequency'],
        ['Budget', '$875,000/month ($3,500,000 total)'],
        ['Flight Dates', 'March 1 - June 30, 2026'],
        ['Target Reach', '5,000,000 unique households'],
        ['Target Frequency', 'Average 3x per week'],
        ['Target CPM', '$15.00 average'],
        ['Format', ':30 and :15 video (non-skippable preferred)'],
    ]

    ctv_table = Table(ctv_overview, colWidths=[1.8*inch, 4.5*inch])
    ctv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ctv_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("4.2 Priority Publishers", styles['SubSection']))
    story.append(Paragraph(
        "We seek premium CTV inventory from the following publishers. Please provide availability "
        "and pricing for each:",
        styles['RivianBody']
    ))

    publisher_data = [
        ['Publisher', 'Priority', 'Content Focus', 'Estimated Monthly Impressions'],
        ['HBO Max / Max', 'Tier 1', 'Premium drama, documentaries', '15,000,000'],
        ['Peacock / NBCUniversal', 'Tier 1', 'Sports, news, entertainment', '20,000,000'],
        ['Paramount+', 'Tier 1', 'Sports, original series', '12,000,000'],
        ['Hulu', 'Tier 1', 'Next-day TV, originals', '18,000,000'],
        ['Disney+', 'Tier 2', 'Family, adventure content', '10,000,000'],
        ['YouTube TV', 'Tier 2', 'Live TV, sports', '8,000,000'],
    ]

    pub_table = Table(publisher_data, colWidths=[1.5*inch, 0.8*inch, 2*inch, 2.2*inch])
    pub_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(pub_table)

    story.append(Paragraph("4.3 CTV Requirements", styles['SubSection']))
    ctv_reqs = [
        "Household-level frequency capping across all publishers",
        "Brand safety: GARM-compliant inventory only",
        "Viewability: 100% in-view, video starts on load",
        "Fraud protection: IVT rate < 1%",
        "Measurement: Cross-platform reach/frequency reporting (Nielsen, Comscore, or equivalent)",
        "Reporting: Weekly delivery reports with publisher and content breakdowns"
    ]
    for req in ctv_reqs:
        story.append(Paragraph(f"\u2022 {req}", styles['BulletText']))
    story.append(PageBreak())

    # Performance Campaign
    story.append(Paragraph("5. PERFORMANCE CAMPAIGN", styles['SectionHeader']))

    story.append(Paragraph("5.1 Campaign Overview", styles['SubSection']))
    perf_overview = [
        ['Parameter', 'Specification'],
        ['Objective', 'Conversion Optimization'],
        ['Budget', '$200,000/month ($800,000 total)'],
        ['Flight Dates', 'March 1 - June 30, 2026'],
        ['Optimization Goal', 'Maximize conversions within budget'],
        ['Conversion Events', '1) Email signup for R2 info, 2) $100 deposit reservation'],
    ]

    perf_table = Table(perf_overview, colWidths=[1.8*inch, 4.5*inch])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("5.2 Formats & Placements", styles['SubSection']))
    format_data = [
        ['Format', 'Sizes/Specs', 'Budget Allocation', 'Placement'],
        ['Desktop Video', ':15, :30 pre-roll', '40%', 'ComScore Top 200 publishers'],
        ['Mobile Web Video', ':15, :30 pre-roll/outstream', '30%', 'ComScore Top 200 publishers'],
        ['Display Banners', '300x250, 728x90, 320x50', '15%', 'Premium news, lifestyle sites'],
        ['Native Ads', 'In-feed, content rec', '15%', 'Premium native networks'],
    ]

    format_table = Table(format_data, colWidths=[1.4*inch, 1.7*inch, 1.2*inch, 2.2*inch])
    format_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(format_table)

    story.append(Paragraph("5.3 Performance Requirements", styles['SubSection']))
    perf_reqs = [
        "Conversion tracking: Server-side pixel implementation required",
        "Attribution: Last-touch attribution with 30-day lookback",
        "Viewability: 70%+ for display, 100% for video",
        "Brand safety: GARM-compliant, no UGC placements",
        "Fraud: IVT < 2% (MRC-accredited verification required)",
        "Reporting: Daily automated reporting with conversion data"
    ]
    for req in perf_reqs:
        story.append(Paragraph(f"\u2022 {req}", styles['BulletText']))
    story.append(PageBreak())

    # Mobile App Campaign
    story.append(Paragraph("6. MOBILE APP INSTALL CAMPAIGN", styles['SectionHeader']))

    story.append(Paragraph("6.1 Campaign Overview", styles['SubSection']))
    app_overview = [
        ['Parameter', 'Specification'],
        ['Objective', 'App Installs & Post-Install Engagement'],
        ['Budget', '$100,000/month ($400,000 total)'],
        ['Flight Dates', 'March 1 - June 30, 2026'],
        ['Target App', 'Rivian Mobile App (iOS & Android)'],
        ['Primary Goal', 'New installs + deep link to R2 content'],
        ['Secondary Goal', 'Re-engagement of existing Rivian owners'],
    ]

    app_table = Table(app_overview, colWidths=[1.8*inch, 4.5*inch])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(app_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("6.2 Campaign Split", styles['SubSection']))
    app_split = [
        ['Segment', 'Budget %', 'Goal', 'Deep Link Destination'],
        ['New User Acquisition', '60%', 'App installs', 'R2 reservation page in-app'],
        ['Existing Owner Re-engagement', '20%', 'App opens', 'R2 feature comparison'],
        ['Prospective Customer Retargeting', '20%', 'App installs', 'R2 configurator in-app'],
    ]

    split_table = Table(app_split, colWidths=[2*inch, 1*inch, 1.3*inch, 2.2*inch])
    split_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(split_table)

    story.append(Paragraph("6.3 Mobile App Requirements", styles['SubSection']))
    app_reqs = [
        "MMP Integration: AppsFlyer (primary) - all events must flow through AppsFlyer",
        "SKAdNetwork compliance for iOS 14.5+ attribution",
        "Deep linking: Branch.io integration for deferred deep links",
        "Fraud prevention: Must support AppsFlyer Protect360",
        "Post-install events: Track app opens, R2 page views, reservation starts",
        "Target CPI: $3.00-5.00 range (varies by platform and audience)"
    ]
    for req in app_reqs:
        story.append(Paragraph(f"\u2022 {req}", styles['BulletText']))
    story.append(PageBreak())

    # Technical Requirements
    story.append(Paragraph("7. TECHNICAL & INTEGRATION REQUIREMENTS", styles['SectionHeader']))

    story.append(Paragraph("7.1 OpenDirect & Programmatic Standards", styles['SubSection']))
    story.append(Paragraph(
        "This campaign will leverage IAB Tech Lab OpenDirect standards for automated media buying. "
        "Partners should be prepared to support:",
        styles['RivianBody']
    ))

    tech_reqs = [
        "<b>OpenDirect 2.1:</b> Direct orders and line item management via API",
        "<b>Deal IDs:</b> Preferred Deals (PD) and Private Marketplace (PMP) activation",
        "<b>DSP Integration:</b> Amazon DSP, The Trade Desk, DV360 deal ID support",
        "<b>AdCOM:</b> IAB AdCOM 1.0 compliant creative and placement specifications",
        "<b>OpenRTB:</b> OpenRTB 2.6 for programmatic transaction data"
    ]
    for req in tech_reqs:
        story.append(Paragraph(f"\u2022 {req}", styles['BulletText']))

    story.append(Paragraph("7.2 Creative Specifications", styles['SubSection']))
    creative_data = [
        ['Format', 'Dimensions', 'Max File Size', 'Specs'],
        ['CTV Video', '1920x1080', '100MB', ':15/:30, H.264, 25fps+'],
        ['Pre-roll Video', '1920x1080', '50MB', ':15/:30, VAST 4.0'],
        ['Display - LB', '728x90', '150KB', 'HTML5, GIF, JPG'],
        ['Display - MPU', '300x250', '150KB', 'HTML5, GIF, JPG'],
        ['Mobile Banner', '320x50', '100KB', 'HTML5, GIF, JPG'],
        ['Native', 'Various', '1MB', '1200x627 hero image'],
    ]

    creative_table = Table(creative_data, colWidths=[1.4*inch, 1.2*inch, 1.1*inch, 2.8*inch])
    creative_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(creative_table)
    story.append(PageBreak())

    # Proposal Requirements
    story.append(Paragraph("8. PROPOSAL REQUIREMENTS", styles['SectionHeader']))

    story.append(Paragraph("8.1 Submission Guidelines", styles['SubSection']))
    submission_reqs = [
        "Submit proposals by <b>February 15, 2026</b>",
        "Proposals should be submitted in PDF format via email to media@horizon-media.com",
        "Include separate sections for each campaign component (CTV, Performance, Mobile App)",
        "Pricing should be provided as both rate card and negotiated rates",
        "Include case studies demonstrating automotive or EV category experience"
    ]
    for req in submission_reqs:
        story.append(Paragraph(f"\u2022 {req}", styles['BulletText']))

    story.append(Paragraph("8.2 Required Proposal Elements", styles['SubSection']))
    elements = [
        "Executive summary and strategic approach",
        "Detailed media plan with reach/frequency projections",
        "Pricing matrix by publisher, format, and targeting",
        "Audience targeting methodology and data sources",
        "Measurement and attribution approach",
        "Brand safety and fraud prevention capabilities",
        "OpenDirect and programmatic integration capabilities",
        "Deal ID and DSP activation support details",
        "Team structure and account management model",
        "Timeline for campaign launch readiness"
    ]
    for elem in elements:
        story.append(Paragraph(f"\u2022 {elem}", styles['BulletText']))

    story.append(Paragraph("8.3 Evaluation Criteria", styles['SubSection']))
    eval_data = [
        ['Criterion', 'Weight'],
        ['Pricing competitiveness', '25%'],
        ['Audience reach and targeting capabilities', '25%'],
        ['Publisher quality and brand safety', '20%'],
        ['Measurement and reporting capabilities', '15%'],
        ['Technical integration (OpenDirect, Deal IDs)', '10%'],
        ['Team experience and account service', '5%'],
    ]

    eval_table = Table(eval_data, colWidths=[4*inch, 1.5*inch])
    eval_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), RIVIAN_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, RIVIAN_GRAY),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(eval_table)

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("--- END OF RFP ---", styles['FooterNote']))
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph(
        "This document is confidential and intended solely for the use of the intended recipient(s). "
        "Unauthorized disclosure, copying, or distribution is prohibited.",
        styles['FooterNote']
    ))

    # Build PDF
    doc.build(story)
    print("Generated: rivian_r2_media_brief.pdf")


if __name__ == "__main__":
    build_document()
