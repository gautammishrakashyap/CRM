# Counselor Management System Documentation

## Overview

The Counselor Management System is a comprehensive solution for managing educational counselors, leads, and communications. It provides a complete platform for counselors to manage their student leads, track communications, monitor performance, and maintain their professional profiles.

## Features

### 🎯 Core Features

1. **Counselor Profile Management**
   - Personal and professional information management
   - Working hours configuration
   - Notification preferences
   - Availability status control

2. **Lead Management**
   - Lead assignment and reassignment
   - Status tracking (new, contacted, interested, converted, etc.)
   - Quality marking (good, bad, future)
   - Search and filtering capabilities
   - Notes and follow-up scheduling

3. **Communication Tracking**
   - Call logging with duration and outcomes
   - Message tracking (email, SMS, WhatsApp)
   - Communication history
   - Performance metrics

4. **Dashboard & Analytics**
   - Real-time statistics
   - Performance metrics
   - Lead status breakdown
   - Follow-up reminders

5. **Notification System**
   - Real-time notifications
   - Bulk messaging for admins
   - Read/unread status tracking

6. **Admin Management**
   - Counselor status management (block/unblock)
   - Performance monitoring
   - Lead reassignment
   - System analytics

## API Endpoints

### Counselor Profile Endpoints (`/api/v1/counselor`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Get counselor profile |
| PUT | `/profile` | Update counselor profile |
| PUT | `/profile/working-hours` | Update working hours |
| PUT | `/profile/notifications` | Update notification preferences |
| GET | `/profile/status` | Get status and availability |
| PUT | `/profile/availability` | Toggle availability |

### Dashboard Endpoints (`/api/v1/counselor/dashboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Get dashboard statistics |
| GET | `/performance` | Get performance metrics |

### Notification Endpoints (`/api/v1/counselor`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | Get notifications |
| PUT | `/notifications/{id}/read` | Mark notification as read |
| GET | `/notifications/unread-count` | Get unread count |

### Lead Management Endpoints (`/api/v1/counselor/leads`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get leads with filtering |
| GET | `/{lead_id}` | Get lead details |
| PUT | `/{lead_id}/status` | Update lead status |
| PUT | `/{lead_id}/quality` | Mark lead quality |
| PUT | `/{lead_id}/reassign` | Reassign lead |
| POST | `/{lead_id}/notes` | Add note to lead |
| PUT | `/{lead_id}/follow-up` | Schedule follow-up |
| GET | `/summary/stats` | Get lead summary stats |

### Communication Endpoints (`/api/v1/counselor/leads`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/{lead_id}/call-log` | Log a call |
| GET | `/{lead_id}/call-logs` | Get call logs |
| POST | `/{lead_id}/send-message` | Send message |
| GET | `/{lead_id}/messages` | Get messages |
| PUT | `/messages/{message_id}/read` | Mark message as read |
| GET | `/{lead_id}/communication-history` | Get full comm history |
| GET | `/stats/communication` | Get communication stats |

### Admin Counselor Management (`/api/v1/admin`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/counselors` | Get all counselors |
| GET | `/counselors/{id}` | Get counselor details |
| PUT | `/counselors/{id}/status` | Update counselor status |
| PUT | `/counselors/{id}/performance` | Update performance metrics |
| POST | `/leads/{lead_id}/reassign` | Admin reassign lead |
| POST | `/notifications/broadcast` | Send bulk notification |
| GET | `/analytics/overview` | Get system analytics |

## Data Models

### Counselor Profile
```python
{
    "user_id": "string",
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "phone": "string",
    "employee_id": "string",
    "department": "string",
    "position": "string",
    "languages": ["English", "Spanish"],
    "specializations": ["Undergraduate", "Graduate"],
    "countries_expertise": ["USA", "Canada"],
    "courses_expertise": ["Computer Science", "MBA"],
    "max_leads_capacity": 50,
    "current_leads_count": 23,
    "status": "active|inactive|blocked",
    "is_available": true,
    "working_hours": {
        "monday": {"start": "09:00", "end": "18:00"},
        "tuesday": {"start": "09:00", "end": "18:00"}
    },
    "notification_preferences": {
        "email_notifications": true,
        "sms_notifications": false,
        "push_notifications": true
    },
    "performance_metrics": {
        "total_calls_made": 150,
        "successful_conversions": 45,
        "average_call_duration": 15.5,
        "conversion_rate": 30.0
    }
}
```

### Lead
```python
{
    "student_name": "John Doe",
    "student_email": "john@example.com",
    "student_phone": "+1234567890",
    "preferred_countries": ["USA", "Canada"],
    "preferred_courses": ["Computer Science"],
    "budget_range": "$50,000-$70,000",
    "academic_background": "Bachelor's in Engineering",
    "status": "new|contacted|interested|converted|lost",
    "quality": "good|bad|future",
    "priority": "high|medium|low",
    "assigned_counselor_id": "counselor_id",
    "last_contact_date": "2024-01-15T10:30:00",
    "next_follow_up": "2024-01-20T14:00:00",
    "notes": ["Initial contact made", "Interested in CS programs"]
}
```

### Call Log
```python
{
    "lead_id": "lead_id",
    "counselor_id": "counselor_id",
    "call_date": "2024-01-15T10:30:00",
    "duration_minutes": 15,
    "outcome": "successful|no_answer|busy|interested",
    "notes": "Discussed program requirements",
    "follow_up_required": true,
    "next_contact_date": "2024-01-20T14:00:00"
}
```

## Authorization & Permissions

### Counselor Role Permissions
- `manage_leads`: Full access to lead management
- `view_own_profile`: View own profile
- `update_own_profile`: Update own profile
- `log_communications`: Log calls and messages
- `view_dashboard`: Access dashboard
- `send_messages`: Send messages to leads
- `schedule_follow_ups`: Manage follow-ups
- `view_notifications`: View notifications

### Admin Permissions
- All counselor permissions
- Manage counselor status (block/unblock)
- Update performance metrics
- Reassign leads
- Send bulk notifications
- View system analytics

## Setup Instructions

### 1. Initialize Counselor Authorization
```python
from app.core.init_counselor_auth import initialize_counselor_authorization

# Run once to set up counselor role and permissions
initialize_counselor_authorization()
```

### 2. Assign Counselor Role to User
```python
from app.core.init_counselor_auth import assign_counselor_role_to_user

# Assign counselor role to a user
assign_counselor_role_to_user(
    user_id="user_id_here",
    granted_by_user_id="admin_user_id"
)
```

### 3. Database Collections
The system uses the following MongoDB collections:
- `counselor_profiles`: Counselor profile data
- `leads`: Student lead information
- `call_logs`: Call tracking data
- `message_logs`: Message tracking data
- `notifications`: Notification system
- `roles`: Role definitions
- `permissions`: Permission definitions
- `user_roles`: User-role assignments

## Usage Examples

### Creating a Counselor Profile
```python
POST /api/v1/counselor/profile
{
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@company.com",
    "phone": "+1234567890",
    "department": "International Admissions",
    "position": "Senior Counselor",
    "languages": ["English", "Spanish"],
    "specializations": ["Graduate Programs"],
    "countries_expertise": ["USA", "Canada"],
    "max_leads_capacity": 60
}
```

### Updating Lead Status
```python
PUT /api/v1/counselor/leads/{lead_id}/status
{
    "status": "interested"
}
```

### Logging a Call
```python
POST /api/v1/counselor/leads/{lead_id}/call-log
{
    "duration_minutes": 20,
    "outcome": "successful",
    "notes": "Student is very interested in MBA program",
    "follow_up_required": true,
    "next_contact_date": "2024-01-25T14:00:00"
}
```

### Filtering Leads
```python
GET /api/v1/counselor/leads?status=interested&country=USA&page=1&limit=10
```

## Error Handling

The API uses standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

Error responses include detailed messages:
```json
{
    "detail": "Access denied. Counselor role required."
}
```

## Security Features

1. **Role-Based Access Control**: Endpoints are protected by role-based permissions
2. **User Authentication**: JWT token-based authentication
3. **Data Validation**: Comprehensive input validation using Pydantic
4. **Authorization Checks**: Counselors can only access their assigned leads
5. **Admin Controls**: Blocking/unblocking capabilities for security

## Performance Features

1. **Pagination**: All list endpoints support pagination
2. **Filtering**: Advanced filtering for leads and counselors
3. **Indexing**: Database indexes on frequently queried fields
4. **Caching**: Performance metrics caching
5. **Bulk Operations**: Bulk notifications and updates

## Monitoring & Analytics

### Dashboard Metrics
- Lead status breakdown
- Follow-ups due today
- Overdue follow-ups
- Performance statistics

### Performance Tracking
- Call duration averages
- Conversion rates
- Target achievement
- Communication volume

### System Analytics (Admin)
- Counselor utilization rates
- Lead assignment rates
- System-wide performance metrics

## Future Enhancements

1. **Real-time Chat**: WebSocket-based real-time communication
2. **AI Insights**: ML-powered lead scoring and recommendations
3. **Mobile App**: Native mobile application
4. **Integration APIs**: Third-party CRM integrations
5. **Advanced Analytics**: Detailed reporting and forecasting
6. **Automated Workflows**: Task automation and triggers

## Support & Troubleshooting

### Common Issues

1. **403 Forbidden**: Ensure user has counselor role assigned
2. **Lead Not Found**: Verify lead is assigned to current counselor
3. **Profile Creation**: Run authorization initialization script first

### Logs
The system provides comprehensive logging for debugging and monitoring.

### Health Checks
Monitor system health through the analytics endpoints.

---

*For additional support or feature requests, please contact the development team.*