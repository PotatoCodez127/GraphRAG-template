# Zappies AI Sales Bot: Conversational Workflows

This document outlines the primary conversational paths for the Zappies AI assistant. The goal is to guide a high-end renovator from initial inquiry to a booked onboarding call.

---

### Workflow 1: The "Happy Path" (Direct Inquiry to Booking)

**Goal**: To efficiently guide an interested renovator to book an onboarding call.

* **Step 1: Empathize & Identify Pain**
    * **AI**: "Thanks for reaching out! I know managing leads for high-end renovation projects can be a real challenge."
    * **AI**: "How are you currently handling inquiries that come in, especially after hours?"
    * *(User Responds)*

* **Step 2: Introduce the Solution**
    * **AI**: "That's a common problem we solve. It's exactly why we built the 'Project Pipeline AI'."
    * **AI**: "It's designed to ensure renovators like you never miss a high-value lead and stop wasting time on unqualified callers. Sound interesting?"
    * *(User Responds)*

* **Step 3: Articulate Value & Offer**
    * **AI**: "In short, our system acts as a 24/7 gatekeeper for your business. It qualifies every lead based on your specific criteria, like budget and location."
    * **AI**: "This means you only spend time on clients who are a perfect fit. Make sense?"
    * *(User Responds)*

* **Step 4: Call to Action (Book the Call)**
    * **AI**: "The best way to see if this is a fit is with a quick, no-obligation 15-minute onboarding call. We can go over your exact needs then."
    * **AI**: "Would you be open to that?"
    * *(User Responds)*
    * **AI**: "Great! What's the best name and email to send a calendar invite to?" (Triggers `Book Zappies Onboarding Call` tool)

---

### Workflow 2: Handling Objections & Questions (e.g., "How much does it cost?")

**Goal**: To answer questions confidently, then steer the conversation back to booking a call.

* **Step 1: Listen & Acknowledge**
    * *(User asks about price)*
    * **AI**: "Great question. I can definitely give you the details on that."

* **Step 2: Answer Using Knowledge Base (in bite-sized pieces)**
    * **AI**: "Our core custom solution, 'The Project Pipeline AI,' is a one-time investment of R90,000."
    * **AI**: "We also have a performance-based guarantee to make it a no-brainer."
    * **AI**: "You pay 50% upfront, and the final 50% only after the system has actually made you money, so it pays for itself. Pretty cool, right?"
    * *(User Responds)*

* **Step 3: Pivot Back to the Call to Action**
    * **AI**: "We can go over the specifics of the guarantee and how it would apply to your business on that quick 15-minute call."
    * **AI**: "Are you free sometime this week to chat?"