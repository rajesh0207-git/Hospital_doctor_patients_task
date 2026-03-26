## Billing Module

### Features
- Billing linked with Doctor, Patient, Appointment
- Auto calculation of total amount
- Prevent duplicate billing
- Transaction-safe operations
- Revenue reporting APIs

### Transaction Flow
1. Validate doctor, patient, appointment
2. Create billing record
3. Update appointment status
4. Commit transaction
5. Rollback on failure

### Reporting APIs
- Revenue per doctor
- Revenue per day
- Filtered billing list
