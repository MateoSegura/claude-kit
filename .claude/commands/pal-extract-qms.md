---
description: Package PAL for customer delivery (defense procurement, SOC 2 auditors)
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# Extract PAL for Customer Delivery

Package the Process Asset Library into a customer-deliverable format suitable
for defense procurement officers, SOC 2 auditors, and CMMC C3PAOs.

## Steps

1. **Ask the user for extraction flavor:**
   Use AskUserQuestion with options:
   - Base (commercial) -- base processes and commercial standards mappings
   - Government (full) -- base + government overlay processes
   - Government (CMMC-focused) -- filtered for CMMC-relevant processes
   - Government (FedRAMP-focused) -- filtered for FedRAMP-relevant processes

2. **Run the extraction:**
   Create a clean output directory with the selected subset of processes and
   mappings, excluding any internal-only content.

3. **Verify the output:**
   - Check that all expected directories were created
   - Verify no internal-only content leaked into the package
   - Confirm process summaries are present and properly formatted

4. **Report to the user:**
   - Show the output directory path
   - List the sections included
   - Note any processes that were excluded and why
   - Suggest next steps (review before sending to customer)

## Extraction Rules

### Always Included
- Process framework overview
- Standards alignment mappings
- Quality attribute summaries (public-safe portions)

### Always Excluded
- Internal research papers
- Internal specs and implementation details
- AI instrumentation files
- .claude/ configuration
- Git history

### Flavor-Specific
- **Base:** Only base processes and ISO/CMMI mappings
- **Gov full:** Base + all PROC-GOV processes + NIST mappings
- **Gov CMMC:** Base + CMMC-relevant PROC-GOV + NIST 800-171 mapping
- **Gov FedRAMP:** Base + FedRAMP-relevant PROC-GOV + NIST 800-53 mapping
