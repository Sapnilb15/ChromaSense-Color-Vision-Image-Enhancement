# Software requirements specification

You fill this file in stage 1 (see `README.md`).

State what the system must do only in this file. Class names and the directory tree go in `architecture.md` and `structure.md`. Do not name prompt files here.

Fill the **Required** sections before any agent runs. **Optional** sections may say `none`. The topics follow ISO/IEC/IEEE 29148:2018.

Source: `docs/ChromaSense_SRS.docx` (November 2026). The ID in parentheses after each statement is that document's ID.

## Required: Identity

ChromaSense: Color Vision Image Enhancement Web App

## Required: Purpose

This specification is for Team BlindSpot, the course instructor, testers, and the agents that generate and implement the build. The build must satisfy the requirements below, and every `must` verification must hold.

## Required: Scope

ChromaSense is a web app that helps people with red–green color vision deficiency (CVD) tell apart details in their own pictures. The user uploads a still PNG or JPEG image, selects a protan or deutan profile and a severity, compares the enhanced image with the original, and downloads the result. The system finds colors that become hard to distinguish under the selected profile and adjusts only those colors in the targeted regions. Everyday photos, charts, maps, and other graphics use the same controls and pipeline, and results can vary with image content. The goal is to help the user identify the same visual details that a viewer with typical color vision sees.

## Required: Product perspective

ChromaSense is a new, self-contained product. It runs on a development server on the local network and processes images on the server. Users reach it with a web browser on the same local network. It calls no external systems, and image processing does not need internet access.

## Required: Users

- People with protan or deutan CVD (can use a web browser, and know or choose their profile) — upload a picture, enhance the confusable colors, compare the result with the original, and download it

## Required: Product functions

- Upload a PNG or JPEG image with the browser file picker
- Reject invalid files with a clear reason
- Select a protan or deutan profile and a severity
- Detect colors that become confusable under the selected profile
- Enhance only the confusable colors in targeted regions
- Compare the original and enhanced images
- Download the enhanced image as a PNG
- Replace the image or change the profile and generate a new result

## Required: Assumptions and dependencies

- Users have a current version of Chrome, Edge, Firefox, or Safari on a desktop or mobile device
- The browser and the server are on the same local network
- Published CVD simulation models are accurate enough to measure simulated perceptual separation
- Display color accuracy depends on the user's device settings

## Required: Out of scope

- AI image description and chart interpretation
- Voice input or output
- Severe low vision support
- Live camera and video
- Calibration or diagnosis of CVD
- Color naming tools
- User accounts and profile sync
- Browser extensions and native mobile apps
- Access from outside the local network
- Tritan and achromatopsia profiles (possible future extensions)
- Presenting output as medical advice, a CVD diagnosis, or an exact reconstruction of typical color perception

## Required: Requirements

| ID | Statement | Priority | Verification |
| --- | --- | --- | --- |
| SRS-FR-001 | The user shall select a PNG or JPEG image with the browser file picker. (FR-01) | must | Valid PNG and JPEG photos, charts, and maps appear in the same workspace. |
| SRS-FR-002 | The app shall reject unsupported, corrupt, oversized, or over-resolution files with a clear reason. (FR-02) | must | Invalid sample files display an error and are not processed. |
| SRS-FR-003 | The user shall select a protan or deutan profile and a severity value between 0 and 1. (FR-03) | must | Both profiles and the slider limits are available and affect processing. |
| SRS-FR-004 | The app shall show the original image before processing and retain it for comparison. (FR-04) | must | The original remains available throughout the session. |
| SRS-FR-005 | The system shall identify colors that become difficult to distinguish under the selected profile. (FR-05) | must | Known red–green test pairs are flagged, and distinct pairs are not. |
| SRS-FR-006 | The system shall produce an enhanced image by adjusting the flagged colors to increase their distinguishability under the selected profile. (FR-06) | must | Simulated separation increases for eligible test pairs. |
| SRS-FR-007 | The system shall leave pixels outside the targeted color regions unchanged, apart from unavoidable file encoding differences. (FR-07) | must | A pixel comparison shows that changes are limited to targeted regions. |
| SRS-FR-008 | The app shall display the original and enhanced images side by side or through a comparison slider. (FR-08) | must | The user can inspect the same image area in both versions. |
| SRS-FR-009 | The app shall state when no confusable color pair was found or when enhancement could not improve a pair. (FR-09) | must | Each case displays a clear message rather than an unexplained result. |
| SRS-FR-010 | The user shall download the enhanced image as a PNG. (FR-10) | must | The downloaded file opens and matches the displayed result. |
| SRS-FR-011 | The user shall replace the image or change the profile and generate a new result. (FR-11) | must | A new image or profile produces an updated result. |
| SRS-NFR-001 | For a valid image within the stated limits, processing shall finish or report a recoverable error within 30 seconds on the documented test host. (NFR-01) | must | Timed runs on the test host meet the limit. |
| SRS-NFR-002 | The browser interface shall support keyboard operation, visible focus, screen reader labels, and layouts usable on desktop and mobile screens. (NFR-02) | must | Keyboard and accessibility walkthroughs complete the main workflow. |
| SRS-NFR-003 | Controls and status messages shall not rely on color alone and shall meet WCAG 2.2 AA text contrast requirements. (NFR-03) | must | Accessibility checks and manual review pass. |
| SRS-NFR-004 | The server shall validate actual file content and limit upload size before image processing. (NFR-04) | must | Renamed non-image files and oversized files are rejected. |
| SRS-NFR-005 | The app shall not require a user account or retain uploaded pictures after the active session ends. (NFR-05) | must | Session cleanup removes the original and processed files. |
| SRS-NFR-006 | The app shall not represent its output as medical advice, a color vision diagnosis, or an exact reconstruction of typical color perception. (NFR-06) | must | Interface copy and help text avoid those claims. |
| SRS-NFR-007 | Enhancement shall improve simulated perceptual separation for at least 80 percent of eligible color pairs for each profile on the held-out test set. (Section 1.1) | must | The acceptance evaluation reports the improved and eligible pair counts for each profile, and the ratio is at least 80 percent. |
| SRS-NFR-008 | The project shall provide professional software documentation: a PEP 257 docstring in Google style on every public module, class, and function, and a documentation set (README, user guide, developer notes for each package, architecture diagrams, changelog) whose content follows ISO/IEC/IEEE 26514:2022 for audience, purpose, task steps, reference completeness, messages, and limits. (Team addition, November 2026) | must | `ruff check .` with the pydocstyle rules reports no findings, and a review of each document against the documentation checklist passes. |

## Optional: External interfaces

**User interface:** one workflow: upload, choose the profile and severity, compare the original and enhanced images, and download.

**Input limits:** still PNG or JPEG, up to 10 MB and 12 megapixels.

**Communication:** the browser reaches the development server over the local network.

## Optional: Logical data

- Profile: protan or deutan, and severity from 0 to 1
- Session image: the uploaded original and the enhanced result, kept only for the active session

## Optional: Performance

- Processing, or a recoverable error, within 30 seconds on the documented test host (SRS-NFR-001)

## Optional: Design constraints

- Images are processed on the server.
- The app runs on a development server reachable over the local network.
- All pages must meet WCAG 2.2 AA text contrast.

## Optional: Software attributes

- Maintainability: documented code and a standard documentation set (SRS-NFR-008)

## Optional: Acceptance plan

From Section 6 of the source document.

1. Before tuning, set aside labeled PNG and JPEG photos, charts, and maps. Identify target regions and reference colors in each image.
2. For each profile, count the pairs that fall below the chosen simulated color-distance threshold in the original.
3. Measure those regions after enhancement with the same profile and severity.
4. Report the improved and eligible counts by profile and image type, with newly confusable pairs and any changes outside the target regions. Record the threshold and severity.
5. Automated checks also cover upload validation, profile selection, and PNG export.
6. For the demo, prepare one question with a known answer for each image. If people with red–green CVD are available, record answer accuracy, completion time, and feedback on original and enhanced images.
