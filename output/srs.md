# Software Requirements Specification (SRS) for SpinCycle

## 1. Project Brief
**Vision:** To be the 'Square for laundromats' by creating a modern, mobile-first platform that provides a seamless, cashless experience for customers and delivers powerful management, analytics, and revenue-generating tools for self-service laundromat owners.

### Project Goals
- Eliminate revenue loss from coin-based machine failures by transitioning to a fully digital, cashless payment system.
- Provide laundromat owners with real-time operational visibility into machine status, revenue, and maintenance needs through a comprehensive dashboard.
- Enhance the customer experience with mobile payments, cycle status notifications, machine availability maps, and loyalty features.
- Increase owner revenue and customer retention through new business models like monthly subscriptions and loyalty programs.
- Improve maintenance efficiency and reduce repair costs by enabling proactive alerts and tracking.
- Deliver actionable business intelligence to owners via detailed analytics and reporting.

### Project Scope
- A customer-facing mobile application and Progressive Web App (PWA).
- An owner/staff-facing web dashboard for management, reporting, and analytics.
- Integration with IoT controllers on washers and dryers to track machine status and control cycles.
- Cashless payment processing via Stripe Connect integration.
- Real-time machine status display (available, in-use, out-of-order) for customers and owners.
- Customer notifications for cycle completion, reminders, and waitlist availability.
- A customer loyalty points system and a monthly subscription model ('Spin Pass').
- Role-based access control (Owner, Manager, Attendant) for the owner dashboard.
- A machine reservation system for corporate or scheduled use.
- A virtual waitlist feature for customers during peak hours.

### Out of Scope
- Offline machine start functionality (post-MVP feature).
- Third-party integrations, such as Slack, Microsoft Teams, or a public developer API (post-MVP).
- Support for right-to-left (RTL) languages at launch.
- Physical manufacturing or design of the IoT controller hardware.
- Processing of cash or coin payments.

### Success Criteria
- Reduce owner-reported revenue loss from payment mechanism failures by at least 10% within 6 months of deployment.
- Achieve 99.9% uptime for all public-facing APIs.
- Attain a 50% adoption rate for cashless payments at participating laundromats within 3 months.
- Onboard at least 10 laundromat locations in the first year.
- Achieve a customer satisfaction score (CSAT) of 85% or higher for the mobile application.
- Demonstrate a 15% reduction in average machine downtime at locations using the maintenance alert feature for 6 months.

## 2. Requirements Specifications

### Functional Requirements

#### REQ-001: The system shall allow a customer to initiate a laundry session for a specific machine by scanning a QR code located on that machine.
- **Rationale:** Provides a quick, frictionless way for customers to select a machine and begin the payment process without manual entry.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "We want to let customers walk in, scan a QR code on any machine, pay from their phone, and get notified when their cycle is done.", `transcript` (SpinCycle Transcript, MARCUS) - "Every machine has a QR code."
- **Acceptance Criteria:**
  - **AC-001-a**:
    - **Given:** a customer has the SpinCycle application open
    - **When:** they scan a valid QR code on a laundry machine
    - **Then:** the application navigates to the control screen for that specific machine.
  - **AC-001-b**:
    - **Given:** a user does not have the app installed
    - **When:** they scan a valid QR code on a laundry machine using their phone's native camera app
    - **Then:** they are directed to the Progressive Web App (PWA) to continue the process.
- **Affected By:** OQ-018

#### REQ-002: The system shall allow customers to pay for laundry cycles using a digital payment method within the application.
- **Rationale:** Core functionality to enable a cashless laundromat, which reduces owner overhead and solves issues like coin jams.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "pay from their phone", `transcript` (SpinCycle Transcript, DANA) - "Going cashless would be huge."
- **Acceptance Criteria:**
  - **AC-002-a**:
    - **Given:** a customer has selected a machine and a cycle type
    - **When:** they provide valid payment information and confirm the transaction
    - **Then:** the payment is successfully processed and the machine is commanded to start.
- **Depends On:** REQ-011
- **Affected By:** OQ-008

#### REQ-003: The system shall send a push notification to the customer's device when their laundry cycle is complete.
- **Rationale:** Improves customer experience by allowing them to leave the premises without worrying about when to return for their laundry.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "and get notified when their cycle is done.", `transcript` (SpinCycle Transcript, MARCUS) - "When the cycle ends, they get a push notification saying "Your laundry is done at Machine W-07.""
- **Acceptance Criteria:**
  - **AC-003-a**:
    - **Given:** a customer has a cycle running
    - **When:** the machine signals the end of the cycle
    - **Then:** the customer receives a push notification indicating the cycle is complete and which machine it was.
- **Depends On:** REQ-008
- **Affected By:** OQ-004

#### REQ-004: The system shall provide a web-based dashboard for laundromat owners and staff.
- **Rationale:** Provides a centralized interface for owners to manage their business, view analytics, and monitor operations.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "On the owner side, Dana and folks like her need a dashboard showing real-time machine status, revenue reports, and maintenance alerts."
- **Acceptance Criteria:**
  - **AC-004-a**:
    - **Given:** an authorized owner or staff member has valid credentials
    - **When:** they navigate to the dashboard URL and log in
    - **Then:** they are presented with the main dashboard interface.
- **Affected By:** OQ-016

#### REQ-005: The owner dashboard shall display the real-time status of all machines in a selected location.
- **Rationale:** Gives owners immediate visibility into their floor operations without needing to be physically present.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "...a dashboard showing real-time machine status...", `transcript` (SpinCycle Transcript, DANA) - "A live floor map — same as the customer but with more detail."
- **Acceptance Criteria:**
  - **AC-005-a**:
    - **Given:** an owner is viewing their location dashboard
    - **When:** a machine becomes idle
    - **Then:** the dashboard updates to show that machine's status as 'idle' within the defined latency threshold.
  - **AC-005-b**:
    - **Given:** an owner is viewing their location dashboard
    - **When:** a customer starts a machine
    - **Then:** the dashboard updates to show that machine's status as 'running' and displays the remaining cycle time.
  - **AC-005-c**:
    - **Given:** an owner is viewing their location dashboard
    - **When:** a machine has a status of 'out of order'
    - **Then:** the dashboard updates to show that machine's status as 'out of order' within the defined latency threshold.
- **Depends On:** REQ-004, REQ-008
- **Affected By:** OQ-007, OQ-009

#### REQ-006: The owner dashboard shall provide access to revenue reports.
- **Rationale:** Allows owners to track financial performance and make informed business decisions.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "...revenue reports...", `transcript` (SpinCycle Transcript, DANA) - "Revenue today versus yesterday versus same day last week."
- **Acceptance Criteria:**
  - **AC-006-a**:
    - **Given:** an owner with financial permissions is logged into the dashboard
    - **When:** they navigate to the revenue reporting section
    - **Then:** they can view key metrics such as revenue for today, yesterday, and the same day last week.
- **Depends On:** REQ-004
- **Affected By:** OQ-012, OQ-005

#### REQ-007: The owner dashboard shall display maintenance alerts for machines that have faulted.
- **Rationale:** Enables proactive maintenance, reducing machine downtime and costly repairs.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "...maintenance alerts.", `transcript` (SpinCycle Transcript, DANA) - "Alerts for machines that have faulted."
- **Acceptance Criteria:**
  - **AC-007-a**:
    - **Given:** an owner is logged into the dashboard
    - **When:** a machine's IoT controller reports a fault code
    - **Then:** a maintenance alert for that machine is displayed on the dashboard.
- **Depends On:** REQ-004

#### REQ-008: The system shall track and report the status of each machine, including 'idle', 'running', and 'out of order'.
- **Rationale:** This is a fundamental capability that underpins real-time maps for customers, dashboards for owners, and notifications.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "Each machine should report whether it's idle, running, or out of order."
- **Acceptance Criteria:**
  - **AC-008-a**:
    - **Given:** a machine is powered on and connected but not in a cycle
    - **When:** the system receives a status update from its IoT controller
    - **Then:** the machine's status is recorded as 'idle'.
  - **AC-008-b**:
    - **Given:** a machine is in an active, paid cycle
    - **When:** the system receives a status update from its IoT controller
    - **Then:** the machine's status is recorded as 'running'.
  - **AC-008-c**:
    - **Given:** a machine reports a critical fault or is manually flagged for maintenance
    - **When:** the system processes this event
    - **Then:** the machine's status is recorded as 'out of order'.
- **Depends On:** REQ-009
- **Affected By:** OQ-007, OQ-006

#### REQ-012: The system shall provide a Progressive Web App (PWA) to allow customers to use the service without installing a native mobile application.
- **Rationale:** Lowers the barrier to entry for new or infrequent customers who may not want to install a full application.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "They open the SpinCycle app — or a progressive web app if they don't want to install anything.", `transcript` (SpinCycle Transcript, MARCUS) - "Scanning it opens the PWA, which handles one-time guest checkout."
- **Acceptance Criteria:**
  - **AC-012-a**:
    - **Given:** a user scans a machine's QR code without the native app installed
    - **When:** they are redirected to the PWA in their mobile browser
    - **Then:** they can complete a payment and start a machine cycle as a guest.

#### REQ-013: The customer application shall display a visual map of the laundromat, color-coding machines by status: green for available, yellow for in-use, and red for out-of-order.
- **Rationale:** Provides customers with an at-a-glance view of machine availability, improving their experience and reducing time spent searching for a free machine.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "They see a map of the location showing which machines are available in green, in-use in yellow, and out-of-order in red."
- **Acceptance Criteria:**
  - **AC-013-a**:
    - **Given:** a customer is viewing the laundromat map
    - **When:** a machine has a status of 'idle'
    - **Then:** it is displayed with a green color indicator.
  - **AC-013-b**:
    - **Given:** a customer is viewing the laundromat map
    - **When:** a machine has a status of 'running'
    - **Then:** it is displayed with a yellow color indicator.
  - **AC-013-c**:
    - **Given:** a customer is viewing the laundromat map
    - **When:** a machine has a status of 'out of order'
    - **Then:** it is displayed with a red color indicator.
- **Depends On:** REQ-008

#### REQ-015: The system shall allow customers to complete a transaction as a guest without creating an account.
- **Rationale:** Reduces friction for first-time or infrequent users.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Scanning it opens the PWA, which handles one-time guest checkout.", `transcript` (SpinCycle Transcript, MARCUS) - "No account required."
- **Acceptance Criteria:**
  - **AC-015-a**:
    - **Given:** a new customer has selected a machine and cycle
    - **When:** they proceed to payment
    - **Then:** they are able to complete the transaction by providing only payment details, without being forced to create a password or user profile.
- **Depends On:** REQ-002

#### REQ-016: The system shall provide an optional customer account that allows access to features like loyalty points.
- **Rationale:** Encourages customer retention and provides a foundation for personalized features.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "if they do create an account they can earn loyalty points."
- **Acceptance Criteria:**
  - **AC-016-a**:
    - **Given:** a customer is using the application
    - **When:** they choose to sign up for an account
    - **Then:** they can create a persistent profile to track their history and loyalty status.
- **Depends On:** REQ-031, REQ-032, REQ-033

#### REQ-017: The system shall implement a loyalty program for registered customers.
- **Rationale:** Incentivizes repeat business and increases customer lifetime value.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "if they do create an account they can earn loyalty points."
- **Acceptance Criteria:**
  - **AC-017-a**:
    - **Given:** a registered customer completes a paid transaction
    - **When:** the payment is successfully processed
    - **Then:** the corresponding number of loyalty points are added to their account.
  - **AC-017-b**:
    - **Given:** a registered customer has accumulated enough points for a reward
    - **When:** they choose to redeem the reward on a qualifying transaction
    - **Then:** the reward is applied and their point balance is debited accordingly.
- **Depends On:** REQ-016

#### REQ-019: The system shall offer a monthly subscription plan ('Spin Pass') for customers.
- **Rationale:** Creates a predictable, recurring revenue stream for laundromat owners and offers value to frequent customers.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "We want a "Spin Pass" monthly subscription option too: twenty-five dollars a month for unlimited standard washes at a single location.", `transcript` (SpinCycle Transcript, DANA) - "I love the subscription idea."
- **Acceptance Criteria:**
  - **AC-019-a**:
    - **Given:** a registered customer is not a subscriber
    - **When:** they navigate to the subscription section and complete the sign-up process
    - **Then:** their account is marked as an active 'Spin Pass' subscriber and they are billed the monthly fee.
  - **AC-019-b**:
    - **Given:** an active 'Spin Pass' subscriber selects a standard wash
    - **When:** they proceed to checkout
    - **Then:** the price is displayed as $0 and they can start the machine without a new charge.
- **Depends On:** REQ-016
- **Affected By:** OQ-013

#### REQ-022: The system shall send a reminder notification to a customer if their completed laundry has not been collected within 5 minutes of the cycle finishing.
- **Rationale:** Helps improve machine turnover by gently nudging customers to retrieve their items, benefiting other waiting customers.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "Five minutes after a cycle ends, if the door hasn't been opened, send the customer a reminder.", `transcript` (SpinCycle Transcript, PRIYA) - "The IoT board can detect door-open events, so we'll know when someone actually unloads."
- **Acceptance Criteria:**
  - **AC-022-a**:
    - **Given:** a customer's laundry cycle has been complete for 5 minutes
    - **When:** the system has not detected a 'door-open' event for that machine
    - **Then:** a reminder push notification is sent to the customer.
  - **AC-022-b**:
    - **Given:** a customer's laundry cycle has been complete for 4 minutes
    - **When:** the customer opens the machine door
    - **Then:** no reminder notification is sent.
- **Depends On:** REQ-003
- **Affected By:** OQ-004

#### REQ-023: The system shall support applying an idle fee for laundry not collected after a pre-defined duration has passed since the cycle's completion.
- **Rationale:** Strongly incentivizes customers to free up machines, maximizing throughput for the laundromat owner.
- **Status:** `confirmed`
- **Priority:** `could`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "After fifteen minutes, start a small idle fee — maybe twenty-five cents per minute — so people have an incentive to come get their stuff."
- **Acceptance Criteria:**
  - **AC-023-a**:
    - **Given:** the idle fee feature is enabled for a location and set to a 15-minute grace period
    - **When:** a machine has been idle with a completed cycle for 15 minutes and 1 second without the door being opened
    - **Then:** the system begins to accrue an idle fee on the customer's account.
  - **AC-023-b**:
    - **Given:** an idle fee is accruing for a customer
    - **When:** the customer opens the machine door
    - **Then:** the system stops accruing the fee and finalizes the total charge.
  - **AC-023-c**:
    - **Given:** an idle fee is accruing at $0.25/min
    - **When:** the customer opens the machine door after 16 minutes and 30 seconds have passed since the cycle completed (1.5 fee-eligible minutes)
    - **Then:** the system finalizes the total charge for 2 full minutes of idle time, for a total of $0.50.
- **Depends On:** REQ-022
- **Affected By:** OQ-014

#### REQ-025: The idle fee feature shall be configurable (enabled/disabled) on a per-location basis by the laundromat owner.
- **Rationale:** Provides flexibility for owners who may want different policies for different locations or may wish to opt out of this feature entirely.
- **Status:** `confirmed`
- **Priority:** `could`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "I'd say we build the notifications and the idle-fee logic but keep the fee togglable per location."
- **Acceptance Criteria:**
  - **AC-025-a**:
    - **Given:** an owner is viewing the settings for one of their locations in the dashboard
    - **When:** they toggle the 'Enable Idle Fee' setting to OFF
    - **Then:** customers at that location will no longer accrue idle fees.
- **Depends On:** REQ-023

#### REQ-026: The owner dashboard shall include a maintenance log for each machine.
- **Rationale:** Allows technicians to track repair history, record notes, and manage the status of machines under repair.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "And a maintenance log where my technician can mark a machine as "under repair" and add notes."
- **Acceptance Criteria:**
  - **AC-026-a**:
    - **Given:** an authorized staff member is viewing a machine's details in the dashboard
    - **When:** they add a new log entry with notes and set the status to 'under repair'
    - **Then:** the machine's status is updated to 'out of order' and the entry is saved in the machine's history.
- **Depends On:** REQ-004
- **Affected By:** OQ-001

#### REQ-027: The system shall implement role-based access control (RBAC) for the owner dashboard to restrict access to data and functionality based on user role.
- **Rationale:** Ensures that staff members only have access to the information and tools necessary for their jobs, protecting sensitive financial data.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "Each location has its own staff, so role-based access is important", `transcript` (SpinCycle Transcript, DANA) - "my floor attendants should see machine status but not revenue numbers."
- **Acceptance Criteria:**
  - **AC-027-a**:
    - **Given:** a user with the 'Attendant' role is logged in
    - **When:** they attempt to access the revenue analytics page
    - **Then:** access is denied.
  - **AC-027-b**:
    - **Given:** a user with the 'Owner' role is logged in
    - **When:** they access the revenue analytics page
    - **Then:** the page is displayed with all data.
- **Depends On:** REQ-004
- **Affected By:** OQ-001, OQ-003

#### REQ-031: The system shall allow customers to register and authenticate using an email address and password.
- **Rationale:** Provides a traditional, standard method for account creation and login.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "For customers, email plus password or social login — Google and Apple."
- **Acceptance Criteria:**
  - **AC-031-a**:
    - **Given:** a new user provides a valid email and password
    - **When:** they submit the registration form
    - **Then:** an account is created and they are logged in.
- **Depends On:** REQ-016

#### REQ-032: The system shall allow customers to register and authenticate using their Google account (social login).
- **Rationale:** Offers a convenient, low-friction authentication method for a large segment of users.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "For customers, email plus password or social login — Google and Apple."
- **Acceptance Criteria:**
  - **AC-032-a**:
    - **Given:** a new user is on the login screen
    - **When:** they click 'Sign in with Google' and successfully authenticate with Google
    - **Then:** a SpinCycle account is created for them and they are logged into the application.
- **Depends On:** REQ-016

#### REQ-033: The system shall allow customers to register and authenticate using their Apple ID (social login).
- **Rationale:** Offers a convenient, low-friction, and privacy-focused authentication method for users in the Apple ecosystem.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "For customers, email plus password or social login — Google and Apple."
- **Acceptance Criteria:**
  - **AC-033-a**:
    - **Given:** a new user is on the login screen on an Apple device
    - **When:** they tap 'Sign in with Apple' and successfully authenticate with Apple
    - **Then:** a SpinCycle account is created for them and they are logged into the application.
- **Depends On:** REQ-016

#### REQ-034: The system shall enforce Time-based One-Time Password (TOTP) two-factor authentication (2FA) for all owner dashboard users.
- **Rationale:** Enhances the security of owner and staff accounts, which have access to sensitive financial and operational data.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "For the owner dashboard we want to enforce two-factor authentication, probably TOTP-based."
- **Acceptance Criteria:**
  - **AC-034-a**:
    - **Given:** a dashboard user has entered their correct username and password
    - **When:** they are prompted for a 2FA code
    - **Then:** they must enter a valid code from their TOTP authenticator app to complete the login.
- **Depends On:** REQ-004

#### REQ-037: The system shall allow customers to request a refund for a transaction through the application.
- **Rationale:** Provides a self-service method for customers to report issues like machine malfunctions and initiate a resolution process.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "If a machine malfunctions mid-cycle, the customer should be able to request a refund from the app."
- **Acceptance Criteria:**
  - **AC-037-a**:
    - **Given:** a customer is viewing their transaction history
    - **When:** they select a transaction and tap the 'Request Refund' option
    - **Then:** a refund request is created and placed in a 'pending' state for manager review.

#### REQ-038: The owner dashboard shall allow authorized users (Manager or Owner) to approve or deny pending refund requests.
- **Rationale:** Gives owners control over the refund process, allowing them to validate requests before funds are returned.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "It goes into a pending state, the location manager approves or denies, and then we process it through Stripe."
- **Acceptance Criteria:**
  - **AC-038-a**:
    - **Given:** a manager is viewing a pending refund request
    - **When:** they click 'Approve'
    - **Then:** the refund is processed via the payment gateway and the request status is updated to 'Approved'.
  - **AC-038-b**:
    - **Given:** a manager is viewing a pending refund request
    - **When:** they click 'Deny'
    - **Then:** the request status is updated to 'Denied' and no refund is issued.
- **Depends On:** REQ-037, REQ-027

#### REQ-040: The system shall allow customers to start machines during an internet outage.
- **Rationale:** Provides maximum uptime and business continuity for the laundromat owner.
- **Status:** `deprecated`
- **Priority:** `wont`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "offline machine start is a post-launch feature."
- **Affected By:** OQ-017

#### REQ-042: The customer-facing application shall support English and Spanish languages.
- **Rationale:** Serves a broader customer base in diverse neighborhoods.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "We serve diverse neighborhoods — English and Spanish at launch, with a localization framework so adding languages later is just a translation file."
- **Acceptance Criteria:**
  - **AC-042-a**:
    - **Given:** a user's device is set to Spanish
    - **When:** they open the SpinCycle application
    - **Then:** all UI text is displayed in Spanish.
  - **AC-042-b**:
    - **Given:** a user's device is set to English
    - **When:** they open the SpinCycle application
    - **Then:** all UI text is displayed in English.

#### REQ-046: The system shall allow customers to join a virtual waitlist for a specific type of machine (e.g., front-load washer) when none are available.
- **Rationale:** Improves customer experience during peak hours by allowing them to queue without physically waiting in the laundromat.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - ""Machine available" — if all machines are busy, a customer can join a virtual waitlist and get notified when one frees up.", `transcript` (SpinCycle Transcript, DANA) - "The waitlist thing would be great."
- **Acceptance Criteria:**
  - **AC-046-a**:
    - **Given:** all machines of a certain type are currently in use
    - **When:** a customer selects that machine type and taps 'Notify me'
    - **Then:** they are added to the end of the virtual waitlist for that machine type.
  - **AC-046-b**:
    - **Given:** a machine becomes available and its waitlist is processed
    - **When:** the last notified user's 5-minute claim window expires without them starting a cycle
    - **Then:** the machine's status becomes generally available to all customers on the map.
- **Depends On:** REQ-008

#### REQ-047: The system shall notify the first customer in a waitlist queue via push notification when a matching machine becomes available.
- **Rationale:** Closes the loop on the waitlist feature, making it useful for the customer.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "When any front-load washer at that location becomes idle, the first person in the queue gets a push notification..."
- **Acceptance Criteria:**
  - **AC-047-a**:
    - **Given:** a customer is first in the waitlist for a front-load washer
    - **When:** a front-load washer's status changes to 'idle'
    - **Then:** that customer receives a push notification and their claim timer begins.
- **Depends On:** REQ-046
- **Affected By:** OQ-004, OQ-010

#### REQ-053: The system shall allow authorized users to reserve a group of specific machines for a defined time window in a single operation.
- **Rationale:** Accommodates corporate or high-value clients who require guaranteed availability for multiple machines at specific times, streamlining the booking process for staff.
- **Status:** `assumed`
- **Priority:** `could`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "They'd love to reserve three washers from six to eight AM.", `client_proxy` (REQ-053 Objection) - "I said I need to 'reserve three washers from six to eight AM' for my corporate clients, implying a single action for a group of machines.", `analyst_inference` (deferred_oq_OQ-019) - "Resolve the critic issue by adopting the current implementation draft for REQ-053."
- **Acceptance Criteria:**
  - **AC-053-a**:
    - **Given:** a laundromat manager is logged into the dashboard
    - **When:** they select three specific washers, a date, and a time window from 6 AM to 8 AM and create a group reservation
    - **Then:** the system records the reservation for all three selected machines.
- **Depends On:** REQ-004
- **Affected By:** OQ-019, OQ-002

#### REQ-054: Reserved machines shall be blocked from general availability in the customer application during their reservation window.
- **Rationale:** Ensures that reservations are honored and reserved machines are not used by other customers.
- **Status:** `confirmed`
- **Priority:** `could`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "It should block those machines from general availability during that window."
- **Acceptance Criteria:**
  - **AC-054-a**:
    - **Given:** a machine is reserved from 6 AM to 8 AM
    - **When:** a general customer views the machine map at 7 AM
    - **Then:** the reserved machine is shown as unavailable (e.g., greyed out or with a 'Reserved' status).
- **Depends On:** REQ-053

#### REQ-056: The owner dashboard shall provide a revenue analytics page with visualizations.
- **Rationale:** Allows owners to understand business trends and performance at a deeper level than simple reports.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "We also want a revenue analytics page: revenue per machine, per cycle type, peak hours heatmap, and average turnaround time."
- **Acceptance Criteria:**
  - **AC-056-a**:
    - **Given:** an owner is viewing the revenue analytics page
    - **When:** they select the 'Peak Hours Heatmap' view
    - **Then:** a visual chart is displayed showing the busiest days and times for their location.
  - **AC-056-b**:
    - **Given:** an owner is viewing the revenue analytics page
    - **When:** they select the 'Revenue by Machine' view
    - **Then:** a report or chart is displayed showing the total revenue generated by each individual machine over the selected time period.
  - **AC-056-c**:
    - **Given:** an owner is viewing the revenue analytics page
    - **When:** they select the 'Revenue by Cycle Type' view
    - **Then:** a report or chart is displayed showing the total revenue generated by each cycle type over the selected time period.
  - **AC-056-d**:
    - **Given:** an owner is viewing the revenue analytics page
    - **When:** they view the summary metrics
    - **Then:** the average machine turnaround time for the selected period is displayed.
- **Depends On:** REQ-006
- **Affected By:** OQ-015

#### REQ-057: The system shall allow owners to export revenue and transaction data to a CSV file.
- **Rationale:** Facilitates offline analysis and integration with external accounting software.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Exportable to CSV for their accountants.", `transcript` (SpinCycle Transcript, DANA) - "I need daily transaction reports for my bookkeeper."
- **Acceptance Criteria:**
  - **AC-057-a**:
    - **Given:** an owner is viewing a revenue report
    - **When:** they click the 'Export to CSV' button
    - **Then:** a CSV file containing the data from the current report view is downloaded to their computer.
- **Depends On:** REQ-006
- **Affected By:** OQ-012, OQ-003

#### REQ-059: The system shall allow administrators to define different laundry cycle types (e.g., Normal, Delicate, Heavy-Duty) with associated prices and durations.
- **Rationale:** This is a necessary prerequisite for allowing customers to choose a cycle and be charged correctly.
- **Status:** `assumed`
- **Priority:** `must`
- **Sources:** `analyst_inference` - "Inferred from the statement: 'They tap an available machine, pick a wash cycle — normal, delicate, heavy-duty — and confirm payment.'"

#### REQ-060: The system shall allow a laundromat owner to send promotional notifications to registered customers of a specific location.
- **Rationale:** Enables owners to run marketing campaigns and drive traffic during off-peak hours, increasing revenue.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Promotional notifications — the owner can push a deal like "free dry with every wash this Thursday.""
- **Acceptance Criteria:**
  - **AC-060-a**:
    - **Given:** an owner is logged into the dashboard
    - **When:** they compose a promotional message and send it to a specific location's customers
    - **Then:** registered customers who have opted into notifications for that location receive the promotional push notification.
- **Depends On:** REQ-004, REQ-016

#### REQ-061: The system shall generate a maintenance alert visible within the owner dashboard when a machine reports a fault.
- **Rationale:** Ensures maintenance issues are addressed promptly by notifying staff via the primary management tool, reducing machine downtime.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "And maintenance alerts to staff when a machine reports a fault code."
- **Acceptance Criteria:**
  - **AC-061-a**:
    - **Given:** a machine's IoT controller publishes a fault code
    - **When:** the system processes the event
    - **Then:** a maintenance alert is generated and associated with the machine and its location.
  - **AC-061-b**:
    - **Given:** an authorized staff member is logged into the dashboard for a specific location
    - **When:** a machine at their location reports a fault
    - **Then:** a persistent, visible alert appears in the dashboard UI until it is acknowledged.
- **Depends On:** REQ-008, REQ-027

### Constraint Requirements

#### REQ-009: The system's IoT controllers shall use the MQTT protocol to communicate status updates to the backend.
- **Rationale:** Defines the specific technology to be used for IoT communication, as determined by the technical team.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "They'll push status over MQTT every ten seconds.", `transcript` (SpinCycle Transcript, PRIYA) - "the IoT boards publish to an MQTT broker."

#### REQ-011: The system shall use Stripe Connect for payment processing to handle fund settlement to individual laundromat owners.
- **Rationale:** Specifies the third-party payment provider and platform (Stripe Connect) to ensure correct routing of funds and simplify PCI compliance.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "For payments we plan to integrate Stripe Connect so each laundromat location is a connected account and funds settle directly to the owner."

#### REQ-051: All network traffic between clients (app, dashboard, IoT) and backend servers must be encrypted using TLS 1.3.
- **Rationale:** Ensures data is secure in transit, protecting against eavesdropping and man-in-the-middle attacks.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "All traffic TLS 1.3."

#### REQ-052: Personally Identifiable Information (PII) must be encrypted at rest using AES-256.
- **Rationale:** Protects sensitive customer data stored in the database from unauthorized access.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "PII encrypted at rest — AES-256."

#### REQ-062: The system backend shall maintain a local payment ledger to ensure the owner dashboard can display revenue data independently of the payment processor's API latency.
- **Rationale:** Guarantees a responsive and available revenue dashboard for owners, even if the primary payment provider's reporting API is slow or temporarily unavailable.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "We'll store a payment ledger locally so the dashboard can show revenue even if Stripe's reporting API is slow."
- **Depends On:** REQ-006

### Non Functional Requirements

#### REQ-010: IoT controllers shall publish a status update at least every 10 seconds.
- **Rationale:** Ensures that the system has a reasonably fresh view of the machine state for real-time dashboards and applications.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** update_frequency - Target: <= 10s (Condition: During normal operation.)
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "They'll push status over MQTT every ten seconds."

#### REQ-014: The system shall physically start a machine's cycle within 5 seconds of a successful payment confirmation.
- **Rationale:** Ensures a responsive and satisfactory user experience, giving the customer immediate feedback that their payment was successful.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** end-to-end_latency - Target: < 5s (Condition: From successful payment API response to machine start command being sent.)
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "The machine starts within five seconds of payment confirmation.", `transcript` (SpinCycle Transcript, PRIYA) - "Payment confirmation to machine start within five seconds — that's end to end including Stripe's authorization round trip."
- **Depends On:** REQ-002

#### REQ-039: The IoT controllers must be able to buffer at least 4 hours of status events to handle network connectivity outages.
- **Rationale:** Ensures data integrity and accurate reporting by preventing data loss during temporary internet disruptions at the laundromat.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** offline_resilience - Target: >= 4 hours (Condition: Buffering of machine status events during network outage.)
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "The boards have a small flash buffer — about four hours of events."

#### REQ-041: The customer-facing application (native and PWA) shall be compliant with Web Content Accessibility Guidelines (WCAG) 2.1 Level AA.
- **Rationale:** Ensures the application is usable by people with a wide range of disabilities, including visual and motor impairments.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** accessibility - Target: WCAG 2.1 AA
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "The app needs to meet WCAG 2.1 AA."

#### REQ-043: Machine status changes must be reflected in the customer and owner applications within 2 seconds of the corresponding event being published by the IoT device.
- **Rationale:** Ensures that the information presented to users is timely and accurate, fostering trust in the system.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** data_freshness_latency - Target: < 2s (Condition: p95 of all status updates from MQTT publish to client UI render.)
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "Machine status updates should reflect in the app within two seconds of the MQTT event."

#### REQ-044: The owner dashboard shall achieve initial data load in under 3 seconds.
- **Rationale:** Provides a responsive and efficient user experience for owners managing their business.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** load_time - Target: < 3s (Condition: On a standard broadband connection (e.g., 25 Mbps).)
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "The dashboard should load initial data in under three seconds on a standard broadband connection."

#### REQ-045: The public-facing APIs shall achieve a monthly uptime of at least 99.9%.
- **Rationale:** Ensures high availability and reliability for the service, which is critical for both customer-facing operations and payment processing.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** availability - Target: >= 99.9% (Condition: Measured monthly.)
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "We're targeting ninety-nine-point-nine percent uptime for the API."

#### REQ-058: The customer API must be rate-limited to 100 requests per minute per user.
- **Rationale:** Prevents system abuse and ensures fair resource allocation among users.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** rate_limit - Target: <= 100 requests/minute (Condition: Per authenticated customer user.)
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "API rate limiting to prevent abuse: a hundred requests per minute per user for the customer API, higher limits for dashboard users."

#### REQ-063: The system API must support at least 500 concurrent users per location without performance degradation.
- **Rationale:** Ensures the system remains stable and responsive during peak usage times at busy laundromat locations.
- **Status:** `confirmed`
- **Priority:** `must`
- **Metric:** concurrency_support - Target: >= 500 users/location (Condition: While maintaining API response times under defined thresholds (e.g., p95 < 500ms).)
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "Load testing to verify the API handles at least five hundred concurrent users per location without degradation."

### Business Rule Requirements

#### REQ-018: Registered customers shall earn one loyalty point for every full dollar spent (e.g., a $3.50 purchase earns 3 points), and can redeem 100 points for a free standard wash.
- **Rationale:** Defines the specific earn and burn rates for the loyalty program, clarifying that points are awarded by flooring the dollar amount of the transaction.
- **Status:** `assumed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Simple tier system. Every dollar spent earns one point.", `transcript` (SpinCycle Transcript, MARCUS) - "At a hundred points you get a free standard wash — roughly a ten-percent rebate.", `analyst_inference` - "Assumed that points are awarded only for whole dollars spent (i.e., a $3.50 purchase earns 3 points) to resolve ambiguity in the transcript."
- **Depends On:** REQ-017

#### REQ-020: The 'Spin Pass' subscription shall provide unlimited standard washes at a single, designated location for a monthly fee of $25.
- **Rationale:** Defines the specific terms, benefits, and price of the subscription plan.
- **Status:** `open`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "twenty-five dollars a month for unlimited standard washes at a single location."
- **Depends On:** REQ-019
- **Affected By:** OQ-013

#### REQ-021: 'Spin Pass' subscribers shall receive a 50% discount on premium cycle types.
- **Rationale:** Adds value to the subscription and encourages upselling to higher-margin cycles.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Premium cycles like sanitize or extra-large would be discounted fifty percent for subscribers."
- **Depends On:** REQ-019

#### REQ-024: Idle fees shall be billed in full-minute increments, where any partial minute incurs the full per-minute charge (e.g., 90 seconds of idle time is billed as 2 minutes). The rate shall be configurable by the owner, with a suggested default of $0.25 per minute.
- **Rationale:** Defines the billing logic and default rate for the idle fee feature, ensuring transparency for the customer.
- **Status:** `confirmed`
- **Priority:** `could`
- **Sources:** `transcript` (SpinCycle Transcript, DANA) - "maybe twenty-five cents per minute", `transcript` (SpinCycle Transcript, PRIYA) - "We should probably bill in full-minute increments and clearly disclose that."
- **Depends On:** REQ-023
- **Affected By:** OQ-014

#### REQ-028: The 'Owner' role shall have full access to all data and functionality for all locations associated with their account, including aggregate views.
- **Rationale:** Defines the permissions for the top-level user role.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Owner sees everything.", `transcript` (SpinCycle Transcript, DANA) - "I need to switch between them or see an aggregate view."
- **Depends On:** REQ-027
- **Affected By:** OQ-011

#### REQ-029: The 'Manager' role shall have full access to all data and functionality, but only for their specifically assigned location(s).
- **Rationale:** Defines the permissions for a location-specific management role.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Manager sees everything for their assigned location."
- **Depends On:** REQ-027

#### REQ-030: The 'Attendant' role shall be able to view machine status and change a machine's status to 'out of order' by creating a maintenance log entry, but shall have no access to financial data.
- **Rationale:** Defines the permissions for a limited, operational-focused role, empowering floor staff to immediately prevent customers from using a broken machine.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Attendant sees machine status and can flag maintenance issues but no financial data.", `client_proxy` (REQ-030 Objection) - "My floor staff needs the ability to put a machine into an 'out of order' state themselves to prevent customers from using a broken machine."
- **Depends On:** REQ-027

#### REQ-035: The platform shall collect a 7% service fee from each transaction, with the remainder settling to the laundromat owner's connected account.
- **Rationale:** Defines the core business model for the SpinCycle platform.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "The platform takes a seven-percent service fee off each transaction, and the remainder settles to the laundromat's connected Stripe account."
- **Depends On:** REQ-002, REQ-011

#### REQ-036: Payouts of collected funds to laundromat owners shall occur on a two-day rolling basis.
- **Rationale:** Sets the expectation for how quickly owners will receive their revenue.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, PRIYA) - "Payouts happen on a two-day rolling basis."
- **Depends On:** REQ-011

#### REQ-048: A customer notified from the waitlist shall have 5 minutes to start a cycle on an available machine. If they do not claim a machine in time, their spot is forfeited and the next person in the queue is notified. If there are no more users in the queue, the machine becomes generally available.
- **Rationale:** Ensures the waitlist moves efficiently and doesn't leave machines idle for extended periods.
- **Status:** `confirmed`
- **Priority:** `should`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "...and has five minutes to start a cycle. If they don't, it moves to the next person."
- **Depends On:** REQ-047

#### REQ-049: All financial transaction data must be retained for a minimum of 7 years.
- **Rationale:** Complies with standard financial and tax auditing requirements.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Transaction data kept for seven years for tax purposes."

#### REQ-050: Raw machine telemetry event data shall be purged after 90 days, but daily aggregated telemetry data shall be retained indefinitely.
- **Rationale:** Manages data storage costs by retaining only valuable long-term data while discarding granular, short-term data.
- **Status:** `confirmed`
- **Priority:** `must`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Machine telemetry — raw events can be purged after ninety days, but daily aggregates kept indefinitely for trend analysis."

#### REQ-055: A 50% cancellation fee shall be charged if a machine reservation is cancelled less than two hours before its scheduled start time, based on a yet-to-be-defined reservation cost.
- **Rationale:** Compensates the owner for lost revenue opportunity from late cancellations. The basis for calculating the fee (e.g., estimated cycle costs, flat fee) is not yet defined.
- **Status:** `assumed`
- **Priority:** `could`
- **Sources:** `transcript` (SpinCycle Transcript, MARCUS) - "Reservations with a configurable cancellation policy — cancel up to two hours before the window, otherwise you're charged fifty percent.", `analyst_inference` (deferred_oq_OQ-020) - "Resolve the critic issue by adopting the current implementation draft for REQ-055."
- **Depends On:** REQ-053
- **Affected By:** OQ-020
