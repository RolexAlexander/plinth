# User Stories

## US-001: Customer Core Experience
**As a** Laundromat Customer
**I want to** to scan a QR code on a machine and pay for a cycle using my phone
**So that** I can start my laundry quickly without needing cash or coins.

- **Priority:** `must`
- **Implements Requirements:** REQ-001, REQ-002, REQ-012, REQ-014, REQ-015, REQ-059
- **Acceptance Criteria:**
  - **AC-500-a**:
    - **Given:** I am a customer at a laundromat and have the SpinCycle app open
    - **When:** I scan the QR code on an available machine and select a cycle type (e.g., 'Normal Wash')
    - **Then:** I am presented with the payment screen for that cycle.
  - **AC-500-b**:
    - **Given:** I have selected a cycle and am on the payment screen
    - **When:** I confirm payment with a valid payment method
    - **Then:** the machine physically starts its cycle within 5 seconds of the confirmation.
  - **AC-500-c**:
    - **Given:** I am a new user without the app installed
    - **When:** I scan a machine's QR code with my phone's camera
    - **Then:** my browser opens the Progressive Web App (PWA) where I can complete the payment as a guest.
- **Edge Cases:**
  - The QR code is damaged or unreadable.
  - The selected machine is in 'out-of-order' or 'running' status.
  - The payment method is declined by the payment gateway.
  - Network connectivity is lost between payment confirmation and the machine start command.

## US-002: Customer Core Experience
**As a** Laundromat Customer
**I want to** to see a real-time map of the laundromat showing machine availability
**So that** I can quickly find an open machine without walking around.

- **Priority:** `must`
- **Implements Requirements:** REQ-013, REQ-008, REQ-043
- **Acceptance Criteria:**
  - **AC-501-a**:
    - **Given:** I have the app open and select a laundromat location
    - **When:** I view the machine map
    - **Then:** all available machines are shown in green.
  - **AC-501-b**:
    - **Given:** I am viewing the machine map
    - **When:** a machine is in an active cycle
    - **Then:** it is shown in yellow.
  - **AC-501-c**:
    - **Given:** I am viewing the machine map
    - **When:** a machine is marked as out of order
    - **Then:** it is shown in red.
  - **AC-501-d**:
    - **Given:** a machine's status changes (e.g., from 'running' to 'idle')
    - **When:** the IoT device sends an update
    - **Then:** the map in my app reflects this change within 2 seconds.
- **Edge Cases:**
  - The map layout does not match the physical layout of the laundromat.
  - The app fails to receive real-time updates due to poor connectivity on my device.

## US-003: Customer Core Experience
**As a** Laundromat Customer
**I want to** to receive a push notification when my laundry cycle is complete
**So that** I can leave the laundromat and return at the right time.

- **Priority:** `must`
- **Implements Requirements:** REQ-003
- **Acceptance Criteria:**
  - **AC-502-a**:
    - **Given:** I have started a laundry cycle and have notifications enabled
    - **When:** the machine signals the end of its cycle
    - **Then:** I receive a push notification on my device that says 'Your laundry is done at Machine W-07' (or similar).
- **Edge Cases:**
  - I have disabled push notifications for the app.
  - The notification is delayed due to mobile network issues.
  - I used guest checkout and am not eligible for push notifications.

## US-004: Customer Core Experience
**As a** Laundromat Customer
**I want to** to receive a reminder if I haven't collected my laundry shortly after it's finished
**So that** I don't forget it and can free up the machine for others.

- **Priority:** `should`
- **Implements Requirements:** REQ-022
- **Acceptance Criteria:**
  - **AC-503-a**:
    - **Given:** my laundry cycle finished 5 minutes ago and I have not opened the machine door
    - **When:** the system checks for unattended laundry
    - **Then:** I receive a reminder push notification.
  - **AC-503-b**:
    - **Given:** my laundry cycle finished 3 minutes ago
    - **When:** I open the machine door to collect my items
    - **Then:** I do not receive a reminder notification.
- **Edge Cases:**
  - The machine's door sensor fails to register that the door was opened.

## US-005: User & Access Management
**As a** Laundromat Customer
**I want to** to create an account using my email, Google, or Apple ID
**So that** I can access features like loyalty points, subscriptions, and my transaction history.

- **Priority:** `should`
- **Implements Requirements:** REQ-016, REQ-031, REQ-032, REQ-033, REQ-052
- **Acceptance Criteria:**
  - **AC-504-a**:
    - **Given:** I am a new user
    - **When:** I choose to sign up with my email and a password
    - **Then:** a new SpinCycle account is created for me.
  - **AC-504-b**:
    - **Given:** I am a new user
    - **When:** I choose to sign up with my Google account and complete the Google auth flow
    - **Then:** a new SpinCycle account linked to my Google ID is created.
  - **AC-504-c**:
    - **Given:** I am a new user on an iOS device
    - **When:** I choose to sign up with my Apple ID and complete the Apple auth flow
    - **Then:** a new SpinCycle account linked to my Apple ID is created.
- **Edge Cases:**
  - I try to register with an email address that is already in use.
  - I cancel the social login process halfway through.
  - The social login provider (Google/Apple) is temporarily unavailable.

## US-006: User & Access Management
**As a** Laundromat Owner (Multi-Location)
**I want to** to log in to my dashboard using two-factor authentication
**So that** my sensitive business and financial data is protected from unauthorized access.

- **Priority:** `must`
- **Implements Requirements:** REQ-004, REQ-034
- **Acceptance Criteria:**
  - **AC-505-a**:
    - **Given:** I am a registered dashboard user and have set up 2FA
    - **When:** I enter my correct email and password on the login page
    - **Then:** I am prompted to enter a 6-digit code from my authenticator app.
  - **AC-505-b**:
    - **Given:** I have been prompted for my 2FA code
    - **When:** I enter the correct, valid code
    - **Then:** I am successfully logged in and redirected to the dashboard.
- **Edge Cases:**
  - I enter an incorrect or expired 2FA code.
  - I have lost access to my 2FA device and need to use a recovery code.
  - The initial setup of 2FA fails.

## US-007: User & Access Management
**As a** Laundromat Owner (Multi-Location)
**I want to** to assign roles (Manager, Attendant) to my staff for each location
**So that** they can only access the information and tools necessary for their jobs.

- **Priority:** `must`
- **Implements Requirements:** REQ-027, REQ-028, REQ-029, REQ-030
- **Acceptance Criteria:**
  - **AC-506-a**:
    - **Given:** I am logged in as an 'Owner'
    - **When:** I assign a staff member the 'Manager' role for 'Location A'
    - **Then:** that user can view all data, including revenue reports, for 'Location A' but not for 'Location B'.
  - **AC-506-b**:
    - **Given:** I am logged in as an 'Owner'
    - **When:** I assign a staff member the 'Attendant' role for 'Location A'
    - **Then:** that user can view the machine status map but cannot access any revenue or financial pages.
  - **AC-506-c**:
    - **Given:** a user with the 'Attendant' role is logged in
    - **When:** they attempt to navigate directly to the URL for the revenue dashboard
    - **Then:** they are shown an 'Access Denied' error page.
- **Edge Cases:**
  - I accidentally assign a user to the wrong location.
  - A manager tries to access data from a location they are not assigned to.
  - An owner tries to create a custom role (which is not supported).

## US-008: Owner Dashboard & Reporting
**As a** Single-Location Laundromat Manager
**I want to** to see a live dashboard of all my machines
**So that** I can monitor my floor's operational status and machine performance in real-time.

- **Priority:** `must`
- **Implements Requirements:** REQ-005, REQ-044
- **Acceptance Criteria:**
  - **AC-507-a**:
    - **Given:** I am logged in and viewing the dashboard
    - **When:** I look at the list or map of machines
    - **Then:** I can see each machine's current status (idle, running, out of order).
  - **AC-507-b**:
    - **Given:** a machine is in the 'running' state
    - **When:** I view its details on the dashboard
    - **Then:** I can see the remaining time in its cycle.
  - **AC-507-c**:
    - **Given:** I have a standard broadband connection
    - **When:** I navigate to the dashboard page
    - **Then:** the initial data for all my machines loads in under 3 seconds.
- **Edge Cases:**
  - The dashboard fails to load if one or more IoT devices are offline.
  - The displayed 'time remaining' is out of sync with the actual machine.

## US-009: Owner Dashboard & Reporting
**As a** Single-Location Laundromat Manager
**I want to** to view key revenue metrics on my dashboard
**So that** I can quickly assess the financial performance of my location.

- **Priority:** `must`
- **Implements Requirements:** REQ-006, REQ-062
- **Acceptance Criteria:**
  - **AC-508-a**:
    - **Given:** I am logged into the dashboard with the 'Manager' or 'Owner' role
    - **When:** I view the main reporting section
    - **Then:** I can see widgets or reports displaying total revenue for today, yesterday, and the same day last week.
  - **AC-508-b**:
    - **Given:** the primary payment provider's API is slow
    - **When:** I load the revenue dashboard
    - **Then:** the data is still served quickly from the local payment ledger.
- **Edge Cases:**
  - The definition of 'today' is not clear regarding the location's timezone.
  - Revenue data for 'same day last week' is not available for a new location.

## US-010: Owner Dashboard & Reporting
**As a** Laundromat Owner (Multi-Location)
**I want to** to access an analytics page with visual reports
**So that** I can identify trends like my busiest hours and most profitable machines.

- **Priority:** `should`
- **Implements Requirements:** REQ-056
- **Acceptance Criteria:**
  - **AC-509-a**:
    - **Given:** I am on the revenue analytics page
    - **When:** I view the peak hours report
    - **Then:** I see a heatmap showing revenue concentration by day of the week and hour of the day.
  - **AC-509-b**:
    - **Given:** I am on the revenue analytics page
    - **When:** I select the 'Revenue per Machine' view for the last 30 days
    - **Then:** I see a bar chart ranking each machine by the total revenue it generated.
  - **AC-509-c**:
    - **Given:** I am on the revenue analytics page
    - **When:** I view the main metrics
    - **Then:** I see the average machine turnaround time for the selected period.
- **Edge Cases:**
  - The data visualizations are difficult to interpret on a mobile device.
  - The date range filtering for analytics is not working correctly.

## US-011: Owner Dashboard & Reporting
**As a** Laundromat Owner (Multi-Location)
**I want to** to export my financial data to CSV files
**So that** I can share it with my accountant and use it in other software.

- **Priority:** `must`
- **Implements Requirements:** REQ-057
- **Acceptance Criteria:**
  - **AC-510-a**:
    - **Given:** I am viewing the daily transaction report
    - **When:** I click the 'Export to CSV' button
    - **Then:** a CSV file containing a line item for each transaction from that day is downloaded.
  - **AC-510-b**:
    - **Given:** I am viewing the monthly summary report for a location
    - **When:** I click 'Export to CSV'
    - **Then:** a CSV file is downloaded containing columns for gross revenue, platform fees, refunds, and net revenue for that month.
- **Edge Cases:**
  - The exported CSV has formatting issues when opened in Excel.
  - The export fails for very large date ranges due to a timeout.

## US-012: Owner Dashboard & Reporting
**As a** Laundromat Owner (Multi-Location)
**I want to** to see a high-level aggregate view of all my locations
**So that** I can monitor the overall health of my business without drilling into each location individually.

- **Priority:** `must`
- **Implements Requirements:** REQ-028
- **Acceptance Criteria:**
  - **AC-511-a**:
    - **Given:** I am logged in as an 'Owner' of multiple locations
    - **When:** I navigate to the aggregate dashboard
    - **Then:** I see a summary card for each location showing its total revenue for the day.
  - **AC-511-b**:
    - **Given:** I am on the aggregate dashboard
    - **When:** I look at a location's summary card
    - **Then:** I see a count of machines currently in 'idle', 'running', and 'out of order' states.
  - **AC-511-c**:
    - **Given:** I am on the aggregate dashboard
    - **When:** I click on a specific location's summary
    - **Then:** I am taken to the detailed dashboard for that location.
- **Edge Cases:**
  - A newly added location does not appear on the aggregate view immediately.
  - The aggregate revenue totals do not match the sum of the individual location reports.

## US-013: Machine & Maintenance Management
**As a** Single-Location Laundromat Manager
**I want to** to be alerted on my dashboard when a machine reports a fault
**So that** I can dispatch a technician quickly and minimize downtime.

- **Priority:** `must`
- **Implements Requirements:** REQ-007, REQ-061
- **Acceptance Criteria:**
  - **AC-512-a**:
    - **Given:** a washer's IoT device detects a drainage error and publishes a fault code
    - **When:** the backend system processes this event
    - **Then:** a new maintenance alert is created and displayed prominently on the dashboard for that location.
  - **AC-512-b**:
    - **Given:** an active maintenance alert exists for Machine D-04
    - **When:** I view the machine status map
    - **Then:** Machine D-04 is marked with a special fault indicator.
- **Edge Cases:**
  - The system generates duplicate alerts for the same ongoing fault.
  - An alert is not cleared automatically after the fault condition is resolved.

## US-014: Machine & Maintenance Management
**As a** Laundromat Attendant
**I want to** to log maintenance activities and notes for a machine
**So that** we have a clear history of all repairs and can track ongoing issues.

- **Priority:** `must`
- **Implements Requirements:** REQ-026, REQ-030
- **Acceptance Criteria:**
  - **AC-513-a**:
    - **Given:** I am logged in as an 'Attendant' and notice a dryer is making a loud noise
    - **When:** I select that dryer in the dashboard, create a new maintenance log entry with the note 'Bad belt', and set its status to 'Under Repair'
    - **Then:** the machine's public status is changed to 'Out of Order' and the note is saved to its history.
  - **AC-513-b**:
    - **Given:** a manager is viewing the maintenance history for that dryer
    - **When:** they review the log
    - **Then:** they can see my entry with the timestamp, my name, and the note.
- **Edge Cases:**
  - Two staff members try to log a maintenance note for the same machine simultaneously.
  - A staff member forgets to change the machine's status back to 'Idle' after a repair is completed.

## US-015: Customer Engagement & Loyalty
**As a** Laundromat Customer
**I want to** to earn loyalty points for my spending and redeem them for free washes
**So that** I feel rewarded for being a frequent customer.

- **Priority:** `should`
- **Implements Requirements:** REQ-017, REQ-018
- **Acceptance Criteria:**
  - **AC-514-a**:
    - **Given:** I am a registered user with an account
    - **When:** I pay for a $4.50 wash cycle
    - **Then:** 4 loyalty points are added to my account balance.
  - **AC-514-b**:
    - **Given:** I have 120 loyalty points in my account
    - **When:** I choose to start a standard wash and select the option to 'Redeem 100 points'
    - **Then:** the cycle starts without charging my payment method and my point balance is reduced to 20.
- **Edge Cases:**
  - I try to redeem points for a premium, non-standard wash cycle.
  - A transaction is refunded, and the earned loyalty points need to be clawed back.

## US-016: Customer Engagement & Loyalty
**As a** Laundromat Customer
**I want to** to subscribe to a monthly 'Spin Pass'
**So that** I can get unlimited standard washes for a fixed price and save money.

- **Priority:** `should`
- **Implements Requirements:** REQ-019, REQ-020, REQ-021
- **Acceptance Criteria:**
  - **AC-515-a**:
    - **Given:** I am a registered customer
    - **When:** I subscribe to the Spin Pass for a specific location
    - **Then:** I am charged the monthly fee of $25.
  - **AC-515-b**:
    - **Given:** I am an active Spin Pass subscriber
    - **When:** I select a standard wash cycle at my designated location
    - **Then:** the cost is shown as $0 and I can start it without a new charge.
  - **AC-515-c**:
    - **Given:** I am an active Spin Pass subscriber
    - **When:** I select a premium 'sanitize' cycle that normally costs $8.00
    - **Then:** the cost is shown as $4.00 (a 50% discount).
- **Edge Cases:**
  - I try to use my subscription benefits at a different location than the one I subscribed to.
  - My monthly subscription payment fails to renew.
  - The price of a 'standard wash' changes after I subscribe.

## US-017: Customer Engagement & Loyalty
**As a** Laundromat Owner (Multi-Location)
**I want to** to send promotional push notifications to my customers
**So that** I can increase business during off-peak hours.

- **Priority:** `should`
- **Implements Requirements:** REQ-060
- **Acceptance Criteria:**
  - **AC-516-a**:
    - **Given:** I am logged into the owner dashboard
    - **When:** I navigate to the promotions tool, type a message like 'Half-price dryers all day Thursday!', and send it to my 'Downtown' location
    - **Then:** all registered customers who have opted-in to notifications for the 'Downtown' location receive the push notification.
- **Edge Cases:**
  - I accidentally send a promotion to the wrong location.
  - The message contains a typo and I need to retract or correct it.
  - A large number of customers have opted out of notifications, limiting the promotion's reach.

## US-018: Refund Management
**As a** Laundromat Customer
**I want to** to request a refund from the app if a machine fails
**So that** I can easily report a problem and get my money back without having to find an attendant.

- **Priority:** `should`
- **Implements Requirements:** REQ-037
- **Acceptance Criteria:**
  - **AC-517-a**:
    - **Given:** a machine I paid for stopped mid-cycle
    - **When:** I go to my transaction history, select that transaction, and tap 'Request Refund'
    - **Then:** my request is submitted and its status is shown as 'Pending Review'.
- **Edge Cases:**
  - I try to request a refund for a transaction that was completed successfully days ago.
  - The app is offline and cannot submit the refund request.

## US-019: Refund Management
**As a** Single-Location Laundromat Manager
**I want to** to review, approve, or deny customer refund requests
**So that** I have full control over issuing refunds for my location.

- **Priority:** `should`
- **Implements Requirements:** REQ-038
- **Acceptance Criteria:**
  - **AC-518-a**:
    - **Given:** a customer has submitted a refund request and it appears in my dashboard queue
    - **When:** I review the details and click 'Approve'
    - **Then:** the refund is processed via Stripe and the request's status is updated to 'Approved'.
  - **AC-518-b**:
    - **Given:** a customer has submitted a refund request
    - **When:** I investigate and determine it is not valid and click 'Deny'
    - **Then:** no refund is issued and the request's status is updated to 'Denied'.
- **Edge Cases:**
  - I approve a refund by mistake and need to undo it.
  - The Stripe API call to process the refund fails.

## US-020: Peak Hour Management
**As a** Laundromat Customer
**I want to** to join a virtual waitlist when all machines are busy
**So that** I can be notified when one is free and don't have to stand around waiting.

- **Priority:** `should`
- **Implements Requirements:** REQ-046, REQ-047, REQ-048
- **Acceptance Criteria:**
  - **AC-519-a**:
    - **Given:** all front-load washers are in use
    - **When:** I tap the 'Notify Me' button for that machine type
    - **Then:** I am added to the waitlist.
  - **AC-519-b**:
    - **Given:** I am first in the waitlist and a front-load washer becomes available
    - **When:** the system detects the machine is free
    - **Then:** I receive a push notification and have 5 minutes to start a cycle on that machine.
  - **AC-519-c**:
    - **Given:** I was notified that a machine is available but did not start a cycle within 5 minutes
    - **When:** my 5-minute window expires
    - **Then:** the next person in the queue is notified, and I lose my spot.
- **Edge Cases:**
  - I join the waitlist but then leave the laundromat and am no longer in range to use the machine.
  - Multiple machines of the same type become free simultaneously.
  - I cancel my spot on the waitlist.

## US-021: System Foundation
**As a** Laundromat Owner (Multi-Location)
**I want to** the system to securely process payments and settle funds to my account
**So that** I can trust the platform with my revenue and get paid reliably.

- **Priority:** `must`
- **Implements Requirements:** REQ-011, REQ-035, REQ-036
- **Acceptance Criteria:**
  - **AC-520-a**:
    - **Given:** a customer completes a $10.00 transaction at my location
    - **When:** the payment is processed by Stripe Connect
    - **Then:** a 7% platform fee ($0.70) is taken, and the remaining $9.30 is allocated to my connected Stripe account.
  - **AC-520-b**:
    - **Given:** funds have been settled to my Stripe Connect account
    - **When:** the configured payout schedule is reached
    - **Then:** the funds are paid out to my business bank account on a two-day rolling basis.
- **Edge Cases:**
  - A customer's payment is subject to a chargeback.
  - My connected Stripe account information is invalid or needs re-verification.
  - There is a delay in the payout from Stripe.

## US-022: System Foundation
**As a** Laundromat Customer
**I want to** to use the application in either English or Spanish
**So that** I can comfortably use the service in my preferred language.

- **Priority:** `must`
- **Implements Requirements:** REQ-042
- **Acceptance Criteria:**
  - **AC-521-a**:
    - **Given:** my phone's operating system language is set to Spanish
    - **When:** I open the SpinCycle app
    - **Then:** all text in the user interface is displayed in Spanish.
  - **AC-521-b**:
    - **Given:** my phone's operating system language is set to French
    - **When:** I open the SpinCycle app
    - **Then:** the user interface defaults to English.
- **Edge Cases:**
  - Some text remains untranslated or is poorly translated.
  - The layout breaks for longer Spanish words compared to their English counterparts.

## US-023: System Foundation
**As a** System Administrator
**I want to** the system to handle data retention and purging correctly
**So that** we comply with legal requirements and manage storage costs efficiently.

- **Priority:** `must`
- **Implements Requirements:** REQ-049, REQ-050
- **Acceptance Criteria:**
  - **AC-522-a**:
    - **Given:** a financial transaction record is 7 years and 1 day old
    - **When:** I query the database
    - **Then:** the record still exists.
  - **AC-522-b**:
    - **Given:** raw IoT telemetry event data is 91 days old
    - **When:** the daily data purge job runs
    - **Then:** that raw event data is deleted from the database.
  - **AC-522-c**:
    - **Given:** raw IoT data from 91 days ago has been purged
    - **When:** an owner views trend analysis reports for that period
    - **Then:** the reports are still available, generated from the retained daily aggregate data.
- **Edge Cases:**
  - The data purge job fails to run, causing excessive data accumulation.
  - A legal hold requires retaining specific data beyond the normal 7-year period.

## US-024: System Foundation
**As a** Product Owner
**I want to** the system to be performant, reliable, secure, and resilient
**So that** it provides a trustworthy and high-quality service to both customers and owners.

- **Priority:** `must`
- **Implements Requirements:** REQ-039, REQ-045, REQ-051, REQ-058, REQ-063, REQ-009, REQ-010
- **Acceptance Criteria:**
  - **AC-523-a**:
    - **Given:** the system is under normal operation
    - **When:** we measure uptime over a calendar month
    - **Then:** the public-facing APIs achieve at least 99.9% availability.
  - **AC-523-b**:
    - **Given:** a laundromat's internet connection goes down
    - **When:** an IoT device on a machine sends status updates via MQTT every 10 seconds
    - **Then:** the device buffers at least 4 hours of these events and replays them when connectivity is restored.
  - **AC-523-c**:
    - **Given:** a single user of the customer API
    - **When:** they make more than 100 requests in a 60-second window
    - **Then:** their subsequent requests receive a '429 Too Many Requests' error.
  - **AC-523-d**:
    - **Given:** a performance test is run
    - **When:** the API is subjected to a load of 500 concurrent users for a single location
    - **Then:** API response times do not degrade beyond established thresholds.
- **Edge Cases:**
  - A large-scale DDoS attack targets the API.
  - An IoT device's buffer overflows during a prolonged internet outage.

## US-025: System Foundation
**As a** Laundromat Customer with a disability
**I want to** the mobile app and PWA to be compliant with WCAG 2.1 AA standards
**So that** I can use the service effectively with assistive technologies like screen readers or high-contrast mode.

- **Priority:** `must`
- **Implements Requirements:** REQ-041
- **Acceptance Criteria:**
  - **AC-524-a**:
    - **Given:** I use a screen reader on my phone
    - **When:** I navigate through the app
    - **Then:** all interactive elements (buttons, links, form fields) are properly labeled and announced.
  - **AC-524-b**:
    - **Given:** I have low vision and enable high-contrast mode
    - **When:** I view the machine map or any other screen
    - **Then:** the text and UI elements meet the minimum color contrast ratios defined by WCAG 2.1 AA.
- **Edge Cases:**
  - A third-party component (like the payment form) is not fully accessible.
  - New features are released that have not yet been audited for accessibility compliance.

## US-026: Peak Hour Management
**As a** Laundromat Owner (Multi-Location)
**I want to** to optionally enable and configure an idle fee for a location
**So that** I can incentivize customers to collect their laundry promptly, increasing machine turnover during busy periods.

- **Priority:** `could`
- **Implements Requirements:** REQ-023, REQ-024, REQ-025
- **Acceptance Criteria:**
  - **AC-525-a**:
    - **Given:** I am in my location's settings page on the dashboard
    - **When:** I enable the 'Idle Fee' toggle and set the rate to $0.25/min with a 15-minute grace period
    - **Then:** the idle fee system is activated for that location with my specified settings.
  - **AC-525-b**:
    - **Given:** the idle fee is enabled and a customer's cycle has been finished for 16 minutes and 30 seconds
    - **When:** the customer opens the machine door
    - **Then:** the system charges them for 2 full minutes of idle time, totaling $0.50.
  - **AC-525-c**:
    - **Given:** I have disabled the 'Idle Fee' toggle for a location
    - **When:** a customer leaves their laundry for 30 minutes after a cycle ends
    - **Then:** they are not charged any idle fee.
- **Edge Cases:**
  - A customer is not clearly notified about the idle fee policy before starting their machine.
  - The door sensor reports an open event incorrectly, stopping the idle fee calculation prematurely.

## US-027: Advanced Features
**As a** Single-Location Laundromat Manager
**I want to** to create a reservation for multiple machines in a single operation
**So that** I can efficiently block out time for my corporate clients who need guaranteed availability.

- **Priority:** `could`
- **Implements Requirements:** REQ-053, REQ-054, REQ-055
- **Acceptance Criteria:**
  - **AC-526-a**:
    - **Given:** I am on the reservations page of the dashboard
    - **When:** I select three specific washers, a date, and a time window of 6 AM to 8 AM, and confirm the reservation
    - **Then:** a single reservation is created that blocks all three machines for that period.
  - **AC-526-b**:
    - **Given:** a reservation exists for washer W-01 from 6 AM to 8 AM
    - **When:** a regular customer views the machine map at 7 AM
    - **Then:** washer W-01 is shown as unavailable or reserved.
  - **AC-526-c**:
    - **Given:** a reservation exists with a start time of 6 AM
    - **When:** I cancel the reservation at 4:01 AM (less than 2 hours before)
    - **Then:** a 50% cancellation fee is charged to the client's account on file.
- **Edge Cases:**
  - I try to reserve a machine that is already part of another reservation at the same time.
  - A regular customer starts a long cycle that overlaps with the beginning of a reservation window.
  - The basis for calculating the 'reservation cost' (for the cancellation fee) is not defined.
