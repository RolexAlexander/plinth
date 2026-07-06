# Traceability Matrix

| Requirement ID | Statement | User Stories | Entities | Open Questions |
| --- | --- | --- | --- | --- |
| REQ-001 | The system shall allow a customer to initiate a laundry session for a specific machine by scanning a QR code located on that machine. | US-001 | ENT-Customer, ENT-Machine | OQ-018 |
| REQ-002 | The system shall allow customers to pay for laundry cycles using a digital payment method within the application. | US-001 | ENT-Customer, ENT-Machine | OQ-008 |
| REQ-003 | The system shall send a push notification to the customer's device when their laundry cycle is complete. | US-003 | ENT-Customer | OQ-004 |
| REQ-004 | The system shall provide a web-based dashboard for laundromat owners and staff. | US-006 | ENT-User, ENT-Staff, ENT-Location | OQ-016 |
| REQ-005 | The owner dashboard shall display the real-time status of all machines in a selected location. | US-008 | ENT-Location, ENT-Machine | OQ-007, OQ-009 |
| REQ-006 | The owner dashboard shall provide access to revenue reports. | US-009 | ENT-Location | OQ-005, OQ-012 |
| REQ-007 | The owner dashboard shall display maintenance alerts for machines that have faulted. | US-013 | ENT-Location, ENT-Machine | - |
| REQ-008 | The system shall track and report the status of each machine, including 'idle', 'running', and 'out of order'. | US-002 | ENT-Customer, ENT-Machine | OQ-006, OQ-007 |
| REQ-009 | The system's IoT controllers shall use the MQTT protocol to communicate status updates to the backend. | US-024 | ENT-Customer | - |
| REQ-010 | IoT controllers shall publish a status update at least every 10 seconds. | US-024 | ENT-Customer, ENT-Machine | - |
| REQ-011 | The system shall use Stripe Connect for payment processing to handle fund settlement to individual laundromat owners. | US-021 | ENT-Location | - |
| REQ-012 | The system shall provide a Progressive Web App (PWA) to allow customers to use the service without installing a native mobile application. | US-001 | ENT-Customer, ENT-Machine | - |
| REQ-013 | The customer application shall display a visual map of the laundromat, color-coding machines by status: green for available, yellow for in-use, and red for out-of-order. | US-002 | ENT-Customer, ENT-Machine | - |
| REQ-014 | The system shall physically start a machine's cycle within 5 seconds of a successful payment confirmation. | US-001 | ENT-User, ENT-Customer, ENT-Machine | - |
| REQ-015 | The system shall allow customers to complete a transaction as a guest without creating an account. | US-001 | ENT-User, ENT-Customer, ENT-Machine, ENT-Transaction | - |
| REQ-016 | The system shall provide an optional customer account that allows access to features like loyalty points. | US-005 | ENT-User, ENT-Customer, ENT-Transaction, ENT-Subscription | - |
| REQ-017 | The system shall implement a loyalty program for registered customers. | US-015 | ENT-Customer | - |
| REQ-018 | Registered customers shall earn one loyalty point for every full dollar spent (e.g., a $3.50 purchase earns 3 points), and can redeem 100 points for a free standard wash. | US-015 | ENT-Customer, ENT-Transaction | - |
| REQ-019 | The system shall offer a monthly subscription plan ('Spin Pass') for customers. | US-016 | ENT-Customer, ENT-Subscription | OQ-013 |
| REQ-020 | The 'Spin Pass' subscription shall provide unlimited standard washes at a single, designated location for a monthly fee of $25. | US-016 | ENT-Customer, ENT-Location, ENT-Subscription | OQ-013 |
| REQ-021 | 'Spin Pass' subscribers shall receive a 50% discount on premium cycle types. | US-016 | ENT-Customer, ENT-Subscription | - |
| REQ-022 | The system shall send a reminder notification to a customer if their completed laundry has not been collected within 5 minutes of the cycle finishing. | US-004 | ENT-Customer, ENT-Machine | OQ-004 |
| REQ-023 | The system shall support applying an idle fee for laundry not collected after a pre-defined duration has passed since the cycle's completion. | US-026 | ENT-Customer, ENT-Location, ENT-Machine | OQ-014 |
| REQ-024 | Idle fees shall be billed in full-minute increments, where any partial minute incurs the full per-minute charge (e.g., 90 seconds of idle time is billed as 2 minutes). The rate shall be configurable by the owner, with a suggested default of $0.25 per minute. | US-026 | ENT-Customer, ENT-Location, ENT-Machine | OQ-014 |
| REQ-025 | The idle fee feature shall be configurable (enabled/disabled) on a per-location basis by the laundromat owner. | US-026 | ENT-Customer, ENT-Location, ENT-Machine | - |
| REQ-026 | The owner dashboard shall include a maintenance log for each machine. | US-014 | ENT-Machine | OQ-001 |
| REQ-027 | The system shall implement role-based access control (RBAC) for the owner dashboard to restrict access to data and functionality based on user role. | US-007 | ENT-User, ENT-Staff, ENT-Location | OQ-001, OQ-003 |
| REQ-028 | The 'Owner' role shall have full access to all data and functionality for all locations associated with their account, including aggregate views. | US-007, US-012 | ENT-User, ENT-Staff, ENT-Location | OQ-011 |
| REQ-029 | The 'Manager' role shall have full access to all data and functionality, but only for their specifically assigned location(s). | US-007 | ENT-User, ENT-Staff, ENT-Location | - |
| REQ-030 | The 'Attendant' role shall be able to view machine status and change a machine's status to 'out of order' by creating a maintenance log entry, but shall have no access to financial data. | US-007, US-014 | ENT-User, ENT-Customer, ENT-Staff, ENT-Location, ENT-Machine | - |
| REQ-031 | The system shall allow customers to register and authenticate using an email address and password. | US-005 | ENT-User, ENT-Customer, ENT-Transaction, ENT-Subscription | - |
| REQ-032 | The system shall allow customers to register and authenticate using their Google account (social login). | US-005 | ENT-User, ENT-Customer, ENT-Transaction, ENT-Subscription | - |
| REQ-033 | The system shall allow customers to register and authenticate using their Apple ID (social login). | US-005 | ENT-User, ENT-Customer, ENT-Transaction, ENT-Subscription | - |
| REQ-034 | The system shall enforce Time-based One-Time Password (TOTP) two-factor authentication (2FA) for all owner dashboard users. | US-006 | ENT-User, ENT-Staff, ENT-Location | - |
| REQ-035 | The platform shall collect a 7% service fee from each transaction, with the remainder settling to the laundromat owner's connected account. | US-021 | ENT-Location, ENT-Transaction | - |
| REQ-036 | Payouts of collected funds to laundromat owners shall occur on a two-day rolling basis. | US-021 | ENT-Location | - |
| REQ-037 | The system shall allow customers to request a refund for a transaction through the application. | US-018 | ENT-Customer, ENT-Machine, ENT-Transaction | - |
| REQ-038 | The owner dashboard shall allow authorized users (Manager or Owner) to approve or deny pending refund requests. | US-019 | ENT-User, ENT-Customer, ENT-Location | - |
| REQ-039 | The IoT controllers must be able to buffer at least 4 hours of status events to handle network connectivity outages. | US-024 | ENT-Customer | - |
| REQ-040 | The system shall allow customers to start machines during an internet outage. | - | ENT-Customer, ENT-Machine | OQ-017 |
| REQ-041 | The customer-facing application (native and PWA) shall be compliant with Web Content Accessibility Guidelines (WCAG) 2.1 Level AA. | US-025 | ENT-Customer | - |
| REQ-042 | The customer-facing application shall support English and Spanish languages. | US-022 | ENT-Customer | - |
| REQ-043 | Machine status changes must be reflected in the customer and owner applications within 2 seconds of the corresponding event being published by the IoT device. | US-002 | ENT-User, ENT-Customer, ENT-Machine | - |
| REQ-044 | The owner dashboard shall achieve initial data load in under 3 seconds. | US-008 | ENT-User, ENT-Location, ENT-Machine | - |
| REQ-045 | The public-facing APIs shall achieve a monthly uptime of at least 99.9%. | US-024 | ENT-Customer | - |
| REQ-046 | The system shall allow customers to join a virtual waitlist for a specific type of machine (e.g., front-load washer) when none are available. | US-020 | ENT-Customer, ENT-Machine | - |
| REQ-047 | The system shall notify the first customer in a waitlist queue via push notification when a matching machine becomes available. | US-020 | ENT-Customer, ENT-Machine | OQ-004, OQ-010 |
| REQ-048 | A customer notified from the waitlist shall have 5 minutes to start a cycle on an available machine. If they do not claim a machine in time, their spot is forfeited and the next person in the queue is notified. If there are no more users in the queue, the machine becomes generally available. | US-020 | ENT-User, ENT-Customer, ENT-Machine | - |
| REQ-049 | All financial transaction data must be retained for a minimum of 7 years. | US-023 | ENT-Transaction | - |
| REQ-050 | Raw machine telemetry event data shall be purged after 90 days, but daily aggregated telemetry data shall be retained indefinitely. | US-023 | ENT-Machine | - |
| REQ-051 | All network traffic between clients (app, dashboard, IoT) and backend servers must be encrypted using TLS 1.3. | US-024 | ENT-Customer | - |
| REQ-052 | Personally Identifiable Information (PII) must be encrypted at rest using AES-256. | US-005 | ENT-User, ENT-Customer, ENT-Transaction, ENT-Subscription | - |
| REQ-053 | The system shall allow authorized users to reserve a group of specific machines for a defined time window in a single operation. | US-027 | ENT-User, ENT-Staff, ENT-Location, ENT-Machine, ENT-Reservation | OQ-002, OQ-019 |
| REQ-054 | Reserved machines shall be blocked from general availability in the customer application during their reservation window. | US-027 | ENT-Customer, ENT-Location, ENT-Machine, ENT-Reservation | - |
| REQ-055 | A 50% cancellation fee shall be charged if a machine reservation is cancelled less than two hours before its scheduled start time, based on a yet-to-be-defined reservation cost. | US-027 | ENT-Location, ENT-Machine, ENT-Reservation | OQ-020 |
| REQ-056 | The owner dashboard shall provide a revenue analytics page with visualizations. | US-010 | ENT-Location, ENT-Machine | OQ-015 |
| REQ-057 | The system shall allow owners to export revenue and transaction data to a CSV file. | US-011 | ENT-Location, ENT-Transaction | OQ-003, OQ-012 |
| REQ-058 | The customer API must be rate-limited to 100 requests per minute per user. | US-024 | ENT-User, ENT-Customer, ENT-Location | - |
| REQ-059 | The system shall allow administrators to define different laundry cycle types (e.g., Normal, Delicate, Heavy-Duty) with associated prices and durations. | US-001 | ENT-Customer, ENT-Machine | - |
| REQ-060 | The system shall allow a laundromat owner to send promotional notifications to registered customers of a specific location. | US-017 | ENT-Customer, ENT-Location | - |
| REQ-061 | The system shall generate a maintenance alert visible within the owner dashboard when a machine reports a fault. | US-013 | ENT-Staff, ENT-Location, ENT-Machine | - |
| REQ-062 | The system backend shall maintain a local payment ledger to ensure the owner dashboard can display revenue data independently of the payment processor's API latency. | US-009 | ENT-Location | - |
| REQ-063 | The system API must support at least 500 concurrent users per location without performance degradation. | US-024 | ENT-User, ENT-Customer, ENT-Location | - |