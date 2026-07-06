# Open Questions

## OQ-001: How is the 'Maintenance Technician' role handled? The transcript mentions a technician using a maintenance log, but the defined RBAC roles are only Owner, Manager, and Attendant. Is this a distinct user role with its own login, or a function performed by a user with an 'Attendant' or 'Manager' role?
- **Status:** `open`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `False`
- **Affects Requirements:** REQ-026, REQ-027
- **Proposed Assumption:** For the initial implementation, the 'Manager' and 'Attendant' roles will have the necessary permissions to update maintenance logs. A dedicated 'Technician' role is not required.
- **Default If Deferred:** `adopt_assumption`

## OQ-002: How do 'corporate clients' interact with the reservation system? Do they have a special login to create or manage their own recurring reservations, or must they always go through a Manager/Owner to book machines?
- **Status:** `open`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `False`
- **Affects Requirements:** REQ-053
- **Proposed Assumption:** Reservations can only be created by users with 'Manager' or 'Owner' permissions via the owner dashboard. There is no external-facing portal for corporate clients in the initial release.
- **Default If Deferred:** `adopt_assumption`

## OQ-003: Is the 'bookkeeper' a direct user of the system? Dana mentions needing reports for her bookkeeper. Should there be a read-only role with access to financial reports, or is the intended workflow for the Owner to export the CSV and send it to them externally?
- **Status:** `open`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `False`
- **Affects Requirements:** REQ-057, REQ-027
- **Proposed Assumption:** The bookkeeper is not a direct user of the system. The workflow is for the Owner/Manager to export the required CSV reports and provide them to the bookkeeper. A dedicated 'Bookkeeper' role is out of scope.
- **Default If Deferred:** `adopt_assumption`

## OQ-004: How do guest users (using the PWA without an account) receive critical time-sensitive notifications like 'cycle complete', 'unattended laundry reminder', or 'waitlist available'? Push notifications typically require app installation and permissions.
- **Status:** `open`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `False`
- **Affects Requirements:** REQ-003, REQ-022, REQ-047
- **Proposed Assumption:** For the initial release, guest users will not receive push notifications. They will see the cycle timer within the PWA after payment. Notifications are a value-add feature that encourages account creation and native app installation.
- **Default If Deferred:** `adopt_assumption`

## OQ-005: What specific data fields need to be captured for each activity type (call, email, meeting)? Are these structured fields (e.g., call duration, outcome) or a single free-text 'notes' field?
- **Status:** `open`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `False`
- **Affects Requirements:** REQ-006
- **Proposed Assumption:** Initially, all activity types will share a common set of fields: Activity Type, Date/Time, and a multi-line Notes field. No type-specific structured fields will be implemented.
- **Default If Deferred:** `adopt_assumption`

## OQ-006: When a deal is reassigned, what are the expected side effects? Should an automatic notification (e.g., email) be sent to the previous and new owners? Should the reassignment event be logged as a formal entry in the deal's activity history?
- **Status:** `open`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `False`
- **Affects Requirements:** REQ-008
- **Proposed Assumption:** Reassignment changes the deal's owner. A system-generated note is automatically added to the deal's activity log (e.g., 'Deal reassigned from Sally to Joe by Mark'). No email or other external notifications will be sent.
- **Default If Deferred:** `adopt_assumption`

## OQ-007: How is a 'team' defined for reporting and permissions? Is it an explicit entity that Admins create and manage, or is it implicitly defined by the user's 'manager' field in their profile?
- **Status:** `answered`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `True`
- **Blocking Rationale:** This decision dictates a core part of the data model and authorization logic. An implicit hierarchy is simpler, while explicit teams are more flexible but require more complex management interfaces and data structures.
- **Affects Requirements:** REQ-005, REQ-008
- **Proposed Assumption:** A team is defined implicitly. Each user has a single 'manager' field. A manager's team consists of all users who report to them. This hierarchy will be used for all reporting and permissions.
- **Default If Deferred:** `adopt_assumption`
- **Answer:** A team is implicitly defined by the Location (laundromat site). A Manager is assigned to a Location, and their team consists of all attendants assigned to that same Location.

## OQ-008: What is the intended relationship between Contacts and Organizations? Can a Contact exist without being associated with an Organization? Can a Contact be associated with multiple Organizations?
- **Status:** `answered`
- **Synthetic Origin:** `analyst_inference`
- **Blocking:** `True`
- **Blocking Rationale:** This is a fundamental data model question. The answer determines whether the relationship is a simple foreign key (one-to-many) or requires a more complex join table (many-to-many), affecting database schema, APIs, and UI.
- **Affects Requirements:** REQ-002
- **Proposed Assumption:** The relationship is one-to-many: an Organization can have many Contacts, but a Contact must belong to exactly one Organization. An Organization must be selected or created before a new Contact can be saved.
- **Default If Deferred:** `adopt_assumption`

## OQ-009: I mentioned that my version of the live floor map should have 'more detail' than the customer's. The spec doesn't define what this extra detail is. To really manage my floor without being there, could this map also show me things like the revenue that machine has generated today, or the cycle type that's currently running?
- **Status:** `open`
- **Synthetic Origin:** `client_proxy`
- **Blocking:** `False`
- **Affects Requirements:** REQ-005
- **Proposed Assumption:** For launch, the 'more detail' will be limited to displaying the exact cycle time remaining (not just a yellow indicator) and the cycle type currently running. Revenue-per-machine on the map is a future enhancement.
- **Default If Deferred:** `adopt_assumption`

## OQ-010: I love the waitlist idea because my customers could 'go grab coffee next door,' and I even said they could 'get a text.' A lot of my customers might not install the app or allow push notifications. To make this truly useful, can we notify them by text message (SMS) in addition to the push notification?
- **Status:** `open`
- **Synthetic Origin:** `client_proxy`
- **Blocking:** `False`
- **Affects Requirements:** REQ-047
- **Proposed Assumption:** SMS notifications are out of scope for the initial launch due to the added complexity and cost of a third-party SMS gateway integration. Notifications will be limited to in-app push notifications for registered users.
- **Default If Deferred:** `adopt_assumption`

## OQ-011: The spec says I'll get an 'aggregate view' for my multiple locations, which is great. But what information will be on it? To get a quick overview, I'd need to see a summary of all locations on one screen, like total revenue for the day, and maybe a count of running vs. idle machines at each location. Can we define what this aggregate dashboard will actually show?
- **Status:** `open`
- **Synthetic Origin:** `client_proxy`
- **Blocking:** `False`
- **Affects Requirements:** REQ-028
- **Proposed Assumption:** The initial aggregate view will be a high-level summary dashboard containing a list of all locations. For each location, it will show total revenue for the day and the number of machines in each state (idle, running, out-of-order). Deeper analysis will require clicking into a specific location's dashboard.
- **Default If Deferred:** `adopt_assumption`

## OQ-012: I mentioned needing reports to make tax time easier. The spec calls for exporting CSVs, but the format is what matters. To 'save me hours,' I really need that monthly summary report to automatically calculate and show columns for gross revenue, SpinCycle fees, refunds issued, and the final net amount, broken down by location. Does the plan for the CSV export include this specific, summarized report?
- **Status:** `open`
- **Synthetic Origin:** `client_proxy`
- **Blocking:** `False`
- **Affects Requirements:** REQ-057, REQ-006
- **Proposed Assumption:** The system will provide a specific 'Monthly Summary' export option that generates a CSV file with the requested columns: Location, Gross Revenue, Platform Fees, Refunds, Net Revenue. A separate 'Transaction Log' export will provide a raw, line-item dump of all transactions.
- **Default If Deferred:** `adopt_assumption`

## OQ-013: Regarding the 'Spin Pass' monthly subscription, what steps will be taken to comply with consumer protection regulations like the Restore Online Shoppers' Confidence Act (ROSCA)?
- **Status:** `open`
- **Synthetic Origin:** `research`
- **Blocking:** `False`
- **Affects Requirements:** REQ-019, REQ-020
- **Proposed Assumption:** The sign-up flow will include a checkbox for users to explicitly consent to the recurring charge, with a clear summary of the price, billing interval, and a link to the cancellation policy provided directly adjacent to the confirmation button. Cancellation will be accessible through the app's main account screen.
- **Default If Deferred:** `adopt_assumption`

## OQ-014: How will the terms of the optional 'idle fee' (grace period, cost per minute) be presented to the customer to ensure they have clearly accepted the terms before starting a machine?
- **Status:** `open`
- **Synthetic Origin:** `research`
- **Blocking:** `False`
- **Affects Requirements:** REQ-023, REQ-024
- **Proposed Assumption:** If a location has the idle fee enabled, the payment confirmation screen will display a clear, concise notice, such as: 'A $0.25/min fee may apply if laundry is not collected within 15 minutes of cycle completion.' The user must proceed past this notice to pay.
- **Default If Deferred:** `adopt_assumption`

## OQ-015: A key performance indicator in the vended laundry industry is 'turns per day' (the number of cycles a machine runs daily). Should this metric be added to the owner's dashboard analytics?
- **Status:** `open`
- **Synthetic Origin:** `research`
- **Blocking:** `False`
- **Affects Requirements:** REQ-056
- **Proposed Assumption:** For the initial launch, 'revenue per machine' is a sufficient proxy for performance. Calculating and displaying 'turns per day' can be added as a post-launch enhancement to the analytics dashboard.
- **Default If Deferred:** `adopt_assumption`

## OQ-016: Major competitors like Cents and CleanCloud offer software to manage full-service 'Wash-Dry-Fold' (WDF) and Pickup/Delivery (P&D) services, not just self-service payments. Is there a risk that focusing exclusively on self-service will limit market adoption among owners who offer these other services?
- **Status:** `open`
- **Synthetic Origin:** `research`
- **Blocking:** `False`
- **Affects Requirements:** REQ-004
- **Proposed Assumption:** The initial target market is self-service-only laundromats or owners for whom self-service is the primary business driver. WDF and P&D management are out of scope and represent a known feature gap that can be addressed in future major releases if market feedback demands it.
- **Default If Deferred:** `adopt_assumption`

## OQ-017: Competitor IoT payment systems (e.g., PayRange, Nayax) often highlight offline functionality that allows customers to start machines even when the laundromat's internet is down. Given that SpinCycle has deferred this feature, has the risk of this competitive disadvantage been assessed with pilot partners?
- **Status:** `open`
- **Synthetic Origin:** `research`
- **Blocking:** `False`
- **Affects Requirements:** REQ-040
- **Proposed Assumption:** The MVP will proceed without offline start capability. The pilot partner (Dana) understands that during an internet outage, no new cycles can be started via the app, and this is an acceptable limitation for the initial rollout.
- **Default If Deferred:** `adopt_assumption`

## OQ-018: Some comparable payment systems use Bluetooth for machine activation in addition to QR codes. Should Bluetooth be considered as a fallback or alternative activation method, which could be more reliable in cases of damaged QR codes or poor lighting?
- **Status:** `open`
- **Synthetic Origin:** `research`
- **Blocking:** `False`
- **Affects Requirements:** REQ-001
- **Proposed Assumption:** The initial release will rely exclusively on QR codes for machine identification and activation. Bluetooth functionality adds hardware and software complexity that is not justified for the MVP.
- **Default If Deferred:** `drop_scope`

## OQ-019: QA Critic Objection: The acceptance criterion (AC-053-a) fails to test the core user need. The stakeholder requested to 'reserve three washers from six to eight AM,' implying a single bulk action. The AC only tests that a reservation is recorded for three machines, but does not validate that it can be accomplished in a 'single operation' as the requirement statement says. A developer could build a UI that passes the test but fails the user by requiring three separate reservation actions. (target: REQ-053)
- **Status:** `deferred`
- **Synthetic Origin:** `reviewer`
- **Blocking:** `True`
- **Blocking Rationale:** QA reviewer flagged blocking defect on REQ-053
- **Affects Requirements:** REQ-053
- **Proposed Assumption:** Resolve the critic issue by adopting the current implementation draft for REQ-053.
- **Default If Deferred:** `adopt_assumption`

## OQ-020: QA Critic Objection: The requirement for a 50% cancellation fee is critically ambiguous because it fails to define what the fee is 50% of. There is no concept of a 'reservation price' or 'expected cycle cost' in the domain model or requirements from which to calculate the fee. This business rule cannot be implemented as written. (target: REQ-055)
- **Status:** `deferred`
- **Synthetic Origin:** `reviewer`
- **Blocking:** `True`
- **Blocking Rationale:** QA reviewer flagged blocking defect on REQ-055
- **Affects Requirements:** REQ-055
- **Proposed Assumption:** Resolve the critic issue by adopting the current implementation draft for REQ-055.
- **Default If Deferred:** `adopt_assumption`
