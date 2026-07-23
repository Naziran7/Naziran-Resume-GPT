import io
import re
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ScoringService:
    def calculate_ats_score(
        self, parsed_data: Dict[str, Any], target_job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate a composite ATS score from 0 to 100 based on resume completeness, formatting, and matching."""
        
        raw_text = parsed_data.get("raw_text", "").lower()
        
        score_breakdown = {
            "contact_info": 0,    # max 10
            "structure": 0,       # max 20
            "skills": 0,          # max 30
            "impact_metrics": 0,  # max 20
            "readability": 0      # max 20
        }
        
        suggestions = []
        
        # 1. Contact Info Scoring (10 points)
        contact_points = 0
        if parsed_data.get("name") and parsed_data["name"] != "Resume Candidate":
            contact_points += 4
        else:
            suggestions.append("Ensure your full name is clearly visible at the top of your resume.")
            
        if parsed_data.get("email"):
            contact_points += 3
        else:
            suggestions.append("Add a professional email address so recruiters can contact you.")
            
        if parsed_data.get("phone"):
            contact_points += 3
        else:
            suggestions.append("Include your phone number with your contact info.")
            
        score_breakdown["contact_info"] = contact_points

        # 2. Structure Check (20 points)
        structure_points = 0
        has_skills = len(parsed_data.get("skills", [])) > 0
        has_edu = len(parsed_data.get("education", [])) > 0
        has_exp = len(parsed_data.get("experience", [])) > 0
        has_certs = len(parsed_data.get("certifications", [])) > 0
        
        if has_skills:
            structure_points += 7
        else:
            suggestions.append("Create a dedicated 'Skills' section listing your technical and soft skills.")
            
        if has_edu:
            structure_points += 7
        else:
            suggestions.append("Include an 'Education' section outlining your degrees and credentials.")
            
        if has_exp:
            structure_points += 6
        else:
            suggestions.append("Include a 'Work Experience' section listing your historical job roles.")
            
        score_breakdown["structure"] = structure_points

        # 3. Skills Scoring (30 points)
        skills_points = 0
        skills_list = [s.get("name", "").lower() for s in parsed_data.get("skills", [])]
        num_skills = len(skills_list)
        
        # Stop words to filter out non-skill keywords from Job Description
        stop_words = {"the", "and", "with", "for", "that", "this", "from", "have", "must", "will", "your", "our", "are", "you", "all", "work", "team", "years", "experience", "ability", "strong", "knowledge", "working", "looking", "candidate", "role", "responsibilities", "requirements", "engineer", "developer", "analyst", "manager"}

        if target_job_description:
            jd_clean = target_job_description.lower()
            jd_keywords = [word for word in re.findall(r"\b[a-z]{3,}\b", jd_clean) if word not in stop_words]
            unique_jd_keywords = set(jd_keywords)
            
            if unique_jd_keywords:
                # Count how many JD requirement keywords appear in the resume's skills or raw text
                matched_jd_keywords = [kw for kw in unique_jd_keywords if kw in raw_text or any(kw in s for s in skills_list)]
                match_ratio = len(matched_jd_keywords) / len(unique_jd_keywords)
                skills_points = int(match_ratio * 30)
            else:
                skills_points = 15
                
            missing_keywords = [kw.title() for kw in unique_jd_keywords if kw not in raw_text and len(kw) > 3][:5]
            if missing_keywords and skills_points < 24:
                suggestions.append(f"Target Role Skill Gap: Add key missing job requirements: {', '.join(missing_keywords)}")
        else:
            # General skill density scoring when no target JD is specified
            if num_skills >= 12:
                skills_points = 25
            elif num_skills >= 8:
                skills_points = 20
            elif num_skills >= 4:
                skills_points = 14
            else:
                skills_points = 8
                suggestions.append("Expand your skills list. Aim for at least 8-12 specific technical proficiencies.")
                
        score_breakdown["skills"] = skills_points

        # 4. Impact Metrics / Action Verbs (20 points)
        impact_points = 0
        raw_text = parsed_data.get("raw_text", "").lower()
        
        # Look for numbers with percentages, currency, or business impact metrics (excluding standalone phone numbers, dates, and zip codes)
        metric_pattern = r"\b\d+\s*%\b|\$\s*\d+[\d,]*[kMB]?|\b\d+\+?\s+(?:\w+\s+){0,2}(?:%\s*growth|increase|decrease|reduction|users|clients|customers|interactions|projects|team|members|budget|revenue|sales|leads|conversions|tickets|apis|systems|applications|transactions|reports|deliverables|tasks)\b"
        metric_matches = re.findall(metric_pattern, raw_text, re.IGNORECASE)
        metrics_found = len(metric_matches)
        
        if metrics_found >= 4:
            impact_points += 10
        elif metrics_found >= 1:
            impact_points += 6
            suggestions.append("Add a few more quantified business metrics (e.g. 'boosted sales by 20%', 'managed $50k budget').")
        else:
            suggestions.append("Quantify your accomplishments with metrics (e.g., 'boosted sales by 20%', 'managed $5k budget').")

        # Multi-domain action verbs check (Engineering, BA, Business, Operations, Product)
        action_verbs = [
            "managed", "led", "developed", "built", "implemented", "designed", "optimized",
            "increased", "decreased", "created", "spearheaded", "accelerated", "analyzed",
            "coordinated", "facilitated", "formulated", "negotiated", "delivered", "executed",
            "architected", "streamlined", "orchestrated", "transformed", "established"
        ]
        verbs_found = sum(1 for verb in action_verbs if verb in raw_text)
        if verbs_found >= 5:
            impact_points += 10
        elif verbs_found >= 2:
            impact_points += 5
            suggestions.append("Use strong action verbs to start your bullet points (e.g., Spearheaded, Optimized, Orchestrated).")
        else:
            suggestions.append("Start your project accomplishments with strong action verbs rather than passive descriptions.")
            
        score_breakdown["impact_metrics"] = impact_points

        # 5. Readability & Length Check (20 points)
        readability_points = 0
        word_count = len(raw_text.split())
        
        # Ideal resume word count is between 400 and 1000 words
        if 400 <= word_count <= 1000:
            readability_points += 15
        elif 200 <= word_count < 400 or 1000 < word_count <= 1500:
            readability_points += 10
            suggestions.append("Adjust resume length. An ideal resume is 1 to 2 pages long (approx. 475-800 words).")
        else:
            suggestions.append("Your resume length is either extremely short or overly long. Prune or expand sections.")

        # Formatting flag (absence of generic placeholders or parsing garbage)
        if "placeholder" not in raw_text and "[insert]" not in raw_text:
            readability_points += 5
            
        score_breakdown["readability"] = readability_points

        # Total ATS Score
        total_score = sum(score_breakdown.values())
        
        # Default safety suggestions if none triggered
        if not suggestions:
            suggestions.append("Excellent resume! Keep it updated with your latest achievements and metrics.")

        feedback = {
            "score_breakdown": score_breakdown,
            "suggestions": suggestions,
            "has_skills": has_skills,
            "has_education": has_edu,
            "has_experience": has_exp,
            "has_certifications": has_certs,
            "word_count": word_count
        }
        
        return {
            "ats_score": total_score,
            "feedback": feedback,
            "extracted_data": {
                "name": parsed_data.get("name"),
                "email": parsed_data.get("email"),
                "phone": parsed_data.get("phone"),
                "skills": parsed_data.get("skills", []),
                "education": parsed_data.get("education", []),
                "experience": parsed_data.get("experience", []),
                "certifications": parsed_data.get("certifications", [])
            }
        }

    def generate_pdf_report(
        self, candidate_name: str, ats_score: int, feedback: Dict[str, Any]
    ) -> bytes:
        """Compile a styled PDF evaluation report using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        
        # Modify existing styles safely to avoid duplicate name crashes
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=15
        )
        
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2D3748")
        )
        
        bullet_style = ParagraphStyle(
            "ReportBullet",
            parent=body_style,
            leftIndent=20,
            firstLineIndent=-10,
            spaceAfter=5
        )
        
        score_text_style = ParagraphStyle(
            "ScoreText",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2F855A") if ats_score >= 70 else colors.HexColor("#C53030")
        )
        
        story = []
        
        # Title
        story.append(Paragraph("NaziranGPT — ATS Score Report", title_style))
        story.append(Paragraph(f"Candidate Profile: <b>{candidate_name}</b>", body_style))
        story.append(Spacer(1, 10))
        
        # Overall Score Box
        score_data = [
            [
                Paragraph(f"<b>Overall ATS Compatibility Score:</b>", body_style),
                Paragraph(f"<b>{ats_score} / 100</b>", score_text_style)
            ]
        ]
        score_table = Table(score_data, colWidths=[200, 300])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 15))
        
        # Score Breakdown Table
        story.append(Paragraph("Category Score Breakdown", section_heading))
        breakdown = feedback.get("score_breakdown", {})
        
        # Mapping for display names
        display_names = {
            "contact_info": "Contact Information (Max 10)",
            "structure": "Layout & Structure (Max 20)",
            "skills": "Skill Density & Match (Max 30)",
            "impact_metrics": "Quantifiable Achievements (Max 20)",
            "readability": "Readability & Length (Max 20)"
        }
        
        breakdown_data = [["Evaluation Section", "Points Awarded"]]
        for key, points in breakdown.items():
            breakdown_data.append([display_names.get(key, key), str(points)])
            
        breakdown_table = Table(breakdown_data, colWidths=[350, 150])
        breakdown_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
        ]))
        story.append(breakdown_table)
        story.append(Spacer(1, 15))
        
        # Recommendations & Actionable Insights
        story.append(Paragraph("Actionable Recommendations", section_heading))
        suggestions = feedback.get("suggestions", [])
        if suggestions:
            for suggest in suggestions:
                story.append(Paragraph(f"&bull; {suggest}", bullet_style))
        else:
            story.append(Paragraph("Your resume checks all core ATS parameters successfully!", body_style))
            
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
