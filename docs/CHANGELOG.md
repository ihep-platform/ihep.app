# Changelog

All notable changes to the IHEP Prospectus and related repository files will be documented in this file.

## [Unreleased]
- Future edits, compliance updates, and structural adjustments.

## [2026-01-07] - Legal Documents & Registration Compliance
### Added
- **Comprehensive Legal Documents**
  - Terms and Conditions of Membership (20KB) - Complete T&C covering eligibility, account security, services, AI features, disclaimers, liability, and dispute resolution
  - Privacy Policy (20KB) - HIPAA-compliant privacy policy detailing data collection, usage, sharing, security measures, and user rights (CCPA/CPRA compliant)
  - Trust Statement (17KB) - Organizational commitment to transparency, data ownership, privacy as a human right, and human-centered AI
  - AI Governance Policy (6.4KB) - Integrated existing policy covering governance structure, AI lifecycle management, NIST AI RMF alignment, and patient rights

- **Legal Pages (Next.js App Router)**
  - `/legal/terms` - Formatted Terms of Service page with SEO metadata
  - `/legal/privacy` - Formatted Privacy Policy page with security details
  - `/legal/ai-governance` - Formatted AI Governance Policy page with risk framework
  - `/legal/trust` - Formatted Trust Statement page with accountability measures
  - `LegalDocument.tsx` component - Reusable wrapper for consistent legal page rendering

- **Registration Form Enhancements**
  - Mandatory checkboxes for Terms of Service and Privacy Policy acceptance
  - Client-side validation preventing form submission without consent
  - Clear error messaging for missing acceptances
  - Links to all legal documents opening in new tabs
  - Acknowledgment text for AI Governance Policy and Trust Statement
  - Submit button disabled state until both required checkboxes are checked

- **Footer Navigation**
  - New "Legal" section with links to all 4 legal documents
  - Updated grid layout to accommodate 5 columns on large screens
  - Consistent styling with existing footer sections

### Security & Compliance
- All legal pages validated for XSS vulnerabilities (no dangerouslySetInnerHTML, eval, or innerHTML)
- No hardcoded secrets or API keys in any files
- Proper TypeScript typing throughout all components
- HIPAA compliance language integrated across all documents
- Clear data handling, privacy disclosures, and user rights outlined
- AI transparency and explainability requirements documented
- Incident response and breach notification protocols established

### Documentation
- Created markdown versions of all legal documents in `/docs/legal/`
- Added co-author attribution to Jason M Jarmacz and Claude by Anthropic
- Comprehensive commit message with security audit details

## [2025-08-24] - Initial Release
### Added
- Created GCP migration architecture with serverless React frontend and BigQuery database
- Configured Terraform infrastructure, Cloud Functions backend, and BigQuery schema for serverless deployment
- Added comprehensive migration guide and deployment scripts for GCP transition
- Implemented enterprise-grade high availability architecture with 6-layer load balancing
- Added multi-zone deployment, auto-scaling, database clustering, and comprehensive monitoring

## [2025-06-13]
### Added
- Initial setup
### Changed
- Updated header logo to new Health Insight Ventures banner design with tree logo
- Updated to refined logo version with golden frame, doubled header height (py-6) and logo size (h-24) for better visibility

## [2025-08-24] - Initial Release
### Added
- **IHEP_Prospectus_TextHeavy_Final.pdf** with full Appendix (Compliance + Framework Mapping Ledger).
- **IHEP_Prospectus_TextHeavy_Final.docx** with full Appendix.
- **IHEP_Compliance_Mapping.xlsx** (flat single-sheet ledger).
- **README.md** updated to reference Appendix inclusion.
- Initial repo scaffold with `/docs/compliance/` folder.
