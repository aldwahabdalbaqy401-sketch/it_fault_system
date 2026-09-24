# وثيقة التحليل الشامل للنظام ونمذجة UML
## نظام إدارة وتتبع بلاغات الأعطال التقنية (IT Fault Management System)

---

## 📌 الفهرس العام
1. [المقدمة وأهداف النظام](#1-المقدمة-وأهداف-النظام)
2. [الجهات الفاعلة ومصفوفة الصلاحيات (Actors & RBAC)](#2-الجهات-الفاعلة-ومصفوفة-الصلاحيات)
3. [مخطط حالات الاستخدام (Use Case Diagram)](#3-مخطط-حالات-الاستخدام-use-case-diagram)
4. [مخطط الأصناف والكائنات (Class Diagram)](#4-مخطط-الأصناف-والكائنات-class-diagram)
5. [مخطط العلاقات الكينونية (ERD - Database Schema)](#5-مخطط-العلاقات-الكينونية-erd)
6. [مخططات التتابع للعمليات الأساسية (Sequence Diagrams)](#6-مخططات-التتابع-sequence-diagrams)
7. [مخطط انتقال الحالات للبلاغ (State Machine Diagram)](#7-مخطط-انتقال-الحالات-state-machine-diagram)
8. [مخطط النشاط وسير العمليات (Activity Diagram)](#8-مخطط-النشاط-وسير-العمليات-activity-diagram)
9. [مخطط المكونات المعمارية (Component Diagram)](#9-مخطط-المكونات-المعمارية-component-diagram)
10. [مخطط النشر والتوزيع (Deployment Diagram)](#10-مخطط-النشر-والتوزيع-deployment-diagram)

---

## 1. المقدمة وأهداف النظام

**نظام إدارة وتتبع الأعطال التقنية** هو نظام سحابي متكامل يهدف إلى أتمتة دورة حياة بلاغات الصيانة والدعم الفني داخل المؤسسات والإدارات، بدءاً من تسجيل البلاغ ومروراً بالجدولة والتوجيه، وصولاً إلى الإصلاح الفني والتقييم والإغلاق مع محادثة لحظية وإشعارات فورية.

### الأهداف الرئيسية:
- **أتمتة البلاغات:** سرعة تسجيل تذاكر الصيانة وإرفاق الصور التوضيحية.
- **إدارة الموارد:** توزيع المهام على الفنيين حسب التخصص والعبء الوظيفي.
- **التتبع الزمني اللحظي:** توثيق لحظات الاستلام، البدء، والانتهاء ومؤشرات الأداء (KPIs).
- **التواصل الفوري:** شات مدمج لكل بلاغ بين المستخدم والفني والإدارة.
- **التقارير التحليلية:** تصدير كشوفات الأعطال بصيغ PDF و Excel مع رسوم بيانية تفاعلية.

---

## 2. الجهات الفاعلة ومصفوفة الصلاحيات

### الممثلون (Actors):
1. **المستخدم العادي (User):** الموظف أو الطالب الذي يقوم بفتح البلاغات ومتابعتها وتقييمها.
2. **الفني التقني (Technician):** المسؤول عن تنفيذ الإصلاح وكتابة التقارير الفنية وقطع الغيار.
3. **المشرف (Supervisor):** المسؤول عن توزيع وإسناد البلاغات ومتابعة أداء الفنيين.
4. **مدير النظام (Admin):** المتحكم الكامل بالمستخدمين، الصلاحيات، الإعدادات، واستخراج التقارير.

### مصفوفة الصلاحيات (RBAC Matrix):
| الوظيفة | المستخدم (User) | الفني (Technician) | المشرف (Supervisor) | المدير (Admin) |
| :--- | :---: | :---: | :---: | :---: |
| تسجيل الدخول وإنشاء حساب | ✅ | ✅ | ✅ | ✅ |
| تقديم بلاغ جديد | ✅ | ✅ | ✅ | ✅ |
| استعراض بلاغاتي فقط | ✅ | ❌ | ❌ | ❌ |
| استعراض المهام المسندة | ❌ | ✅ | ✅ | ✅ |
| استعراض كل البلاغات | ❌ | ❌ | ✅ | ✅ |
| إسناد وجدولة البلاغ | ❌ | ❌ | ✅ | ✅ |
| بدء المعالجة وحل العطل | ❌ | ✅ | ✅ | ✅ |
| تقييم الخدمة (نجوم) | ✅ (صاحب البلاغ) | ❌ | ❌ | ❌ |
| استخدام شات البلاغ | ✅ (بلاغاته) | ✅ (المسند له) | ✅ | ✅ |
| إدارة المستخدمين والأدوار | ❌ | ❌ | ❌ | ✅ |
| تصدير التقارير (PDF/Excel) | ❌ | ❌ | ✅ | ✅ |

---

## 3. مخطط حالات الاستخدام (Use Case Diagram)

```mermaid
graph TD
    User((المستخدم))
    Tech((الفني))
    Super((المشرف))
    Admin((مدير النظام))

    subgraph "نظام إدارة وتتبع الأعطال التقنية"
        UC1[تسجيل الدخول / استعادة كلمة المرور]
        UC2[تقديم بلاغ عطل جديد مع المرفقات]
        UC3[متابعة مسار التذكرة والخط الزمني]
        UC4[المحادثة الفورية حول البلاغ]
        UC5[تقييم الخدمة 1-5 نجوم]
        
        UC6[استعراض المهام المسندة]
        UC7[بدء المعالجة وتسجيل الملاحظات]
        UC8[حل العطل وإرفاق تقرير الصيانة]
        
        UC9[إسناد العطل لفني وجدولته]
        UC10[متابعة مؤشرات أداء الفنيين]
        UC11[تصدير التقارير PDF / Excel]
        
        UC12[إدارة حسابات المستخدمين والصلاحيات]
        UC13[مراقبة سجل التدقيق والنشاطات]
    end

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5

    Tech --> UC1
    Tech --> UC6
    Tech --> UC7
    Tech --> UC8
    Tech --> UC4

    Super --> UC1
    Super --> UC9
    Super --> UC10
    Super --> UC11
    Super --> UC3
    Super --> UC4

    Admin --> UC1
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
```

---

## 4. مخطط الأصناف والكائنات (Class Diagram)

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string password_hash
        +string full_name
        +string email
        +string phone
        +string department
        +string user_type
        +Role role
        +datetime created_at
        +verify_password(password) bool
        +change_password(new_pass) bool
        +update_profile(data) bool
    }

    class Role {
        <<enumeration>>
        ADMIN
        SUPERVISOR
        TECHNICIAN
        USER
    }

    class Fault {
        +int id
        +string title
        +string description
        +string fault_type
        +string location
        +Priority priority
        +Status status
        +string attachment
        +int user_id
        +int assigned_to
        +datetime scheduled_date
        +datetime received_at
        +datetime started_at
        +datetime completed_at
        +string technician_notes
        +int user_rating
        +datetime created_at
        +datetime updated_at
        +assign(tech_id, date) void
        +start_work() void
        +resolve(notes) void
        +rate(stars) void
        +close() void
    }

    class Priority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        CRITICAL
    }

    class Status {
        <<enumeration>>
        NEW
        IN_PROGRESS
        RESOLVED
        CLOSED
    }

    class ChatMessage {
        +int id
        +int fault_id
        +int sender_id
        +int receiver_id
        +string message
        +string image
        +bool is_read
        +datetime created_at
        +mark_as_read() void
    }

    class Notification {
        +int id
        +int user_id
        +int fault_id
        +string message
        +bool is_read
        +datetime created_at
        +mark_read() void
    }

    class ActivityLog {
        +int id
        +int user_id
        +string username
        +string action
        +string details
        +string ip_address
        +datetime created_at
    }

    User "1" --> "0..*" Fault : submits
    User "1" --> "0..*" Fault : is_assigned_to
    Fault "1" --> "0..*" ChatMessage : contains
    User "1" --> "0..*" ChatMessage : sends
    Fault "1" --> "0..*" Notification : generates
    User "1" --> "0..*" Notification : receives
    User "1" --> "0..*" ActivityLog : triggers
```

---

## 5. مخطط العلاقات الكينونية (ERD)

```mermaid
erDiagram
    USERS ||--o{ FAULTS : "submits (user_id)"
    USERS ||--o{ FAULTS : "assigned (assigned_to)"
    USERS ||--o{ CHAT_MESSAGES : "sends (sender_id)"
    USERS ||--o{ NOTIFICATIONS : "receives (user_id)"
    USERS ||--o{ ACTIVITY_LOG : "performs (user_id)"
    
    FAULTS ||--o{ CHAT_MESSAGES : "hosts (fault_id)"
    FAULTS ||--o{ NOTIFICATIONS : "triggers (fault_id)"

    USERS {
        int id PK
        varchar username UK
        varchar password
        varchar full_name
        varchar email UK
        varchar phone
        varchar department
        varchar user_type
        enum role
        timestamp created_at
    }

    FAULTS {
        int id PK
        varchar title
        text description
        varchar fault_type
        varchar location
        enum priority
        enum status
        varchar attachment
        int user_id FK
        int assigned_to FK
        timestamp scheduled_date
        timestamp received_at
        timestamp started_at
        timestamp completed_at
        text technician_notes
        tinyint user_rating
        timestamp created_at
        timestamp updated_at
    }

    CHAT_MESSAGES {
        int id PK
        int fault_id FK
        int sender_id FK
        int receiver_id FK
        text message
        varchar image
        boolean is_read
        timestamp created_at
    }

    NOTIFICATIONS {
        int id PK
        int user_id FK
        int fault_id FK
        text message
        boolean is_read
        timestamp created_at
    }

    ACTIVITY_LOG {
        int id PK
        int user_id FK
        varchar username
        varchar action
        text details
        varchar ip_address
        timestamp created_at
    }
```

---

## 6. مخططات التتابع (Sequence Diagrams)

### 6.1 دورة تقديم بلاغ جديد (Submit Fault)

```mermaid
sequenceDiagram
    autonumber
    actor User as المستخدم
    participant Browser as المتصفح
    participant App as خادم التطبيق (Flask)
    participant DB as قاعدة البيانات
    participant Mail as خادم البريد

    User->>Browser: تعبئة نموذج البلاغ ورفع المرفق
    Browser->>App: POST /add-fault (بيانات + CSRF Token)
    App->>App: فحص الحقول وتأمين اسم الملف المرفق
    App->>DB: INSERT INTO faults (...) RETURNING id
    DB-->>App: fault_id = 101
    App->>DB: INSERT INTO notifications (للمشرفين والمدير)
    App->>DB: INSERT INTO activity_log (تسجيل الحركة)
    par إشعار بريدي
        App->>Mail: إرسال بريد بتفاصيل البلاغ الجديد
    end
    App-->>Browser: توجيه إلى صفحة تفاصيل العطل /fault/101
    Browser-->>User: إظهار رقم التتبع ورسالة التأكيد
```

### 6.2 دورة الإسناد والمعالجة والحل (Assignment & Resolution)

```mermaid
sequenceDiagram
    autonumber
    actor Super as المشرف
    actor Tech as الفني
    actor User as المستخدم
    participant App as التطبيق
    participant DB as قاعدة البيانات

    Super->>App: إسناد البلاغ للفني وتحديد الموعد
    App->>DB: UPDATE faults SET assigned_to=Tech_ID, scheduled_date=Date
    App->>DB: INSERT INTO notifications (تنبيه الفني)
    
    Tech->>App: فتح البلاغ والضغط على "بدء المعالجة"
    App->>DB: UPDATE faults SET status='in_progress', started_at=NOW()
    
    Tech->>App: إدخال الملاحظات الفنية والضغط على "تم الحل"
    App->>DB: UPDATE faults SET status='resolved', completed_at=NOW(), technician_notes=...
    App->>DB: INSERT INTO notifications (إشعار المستخدم باكتمال الحل)
    
    User->>App: تقييم جودة الخدمة (5 نجوم)
    App->>DB: UPDATE faults SET user_rating=5, status='closed'
    App-->>User: تم إغلاق التذكرة بنجاح وشكراً لتقييمكم
```

---

## 7. مخطط انتقال الحالات (State Machine Diagram)

```mermaid
stateDiagram-v2
    [*] --> New : تقديم البلاغ
    
    state New {
        [*] --> Unassigned : بانتظار المراجعة
        Unassigned --> Assigned : تم الإسناد لفني
    }
    
    New --> InProgress : الفني يبدأ العمل (started_at)
    
    state InProgress {
        [*] --> UnderDiagnosis : الفحص والتشخيص
        UnderDiagnosis --> UnderRepair : تنفيذ الصيانة
    }
    
    InProgress --> Resolved : الفني يكمل الإصلاح (completed_at)
    
    Resolved --> InProgress : إعادة فتح في حال عدم الرضا
    Resolved --> Closed : المستخدم يقيم أو المشرف يغلق التذكرة
    
    Closed --> [*] : أرشفة التذكرة وحساب مؤشرات الأداء
```

---

## 8. مخطط النشاط وسير العمليات (Activity Diagram)

```mermaid
flowchart TD
    Start([بداية]) --> Login[تسجيل دخول المستخدم]
    Login --> Submit[تقديم بلاغ عطل جديد]
    Submit --> Save[حفظ البلاغ كـ New وإشعار الإدارة]
    
    Save --> Assign[إسناد البلاغ وتحديد موعد من المشرف]
    Assign --> TechTake[استلام الفني للبلاغ وبدء المعالجة In Progress]
    
    TechTake --> Fix[إجراء أعمال الصيانة والتواصل عبر الشات عند الحاجة]
    Fix --> Done[تسجيل تقرير الإصلاح وتغيير الحالة إلى Resolved]
    
    Done --> UserRate{معاينة المستخدم للخدمة}
    UserRate -->|غير مكتمل| Reopen[إعادة فتح البلاغ والمتابعة]
    Reopen --> TechTake
    UserRate -->|ناجح ومكتمل| Closed[تقييم الخدمة وإغلاق البلاغ Closed]
    
    Closed --> End([نهاية الدورة المستندية])
```

---

## 9. مخطط المكونات المعمارية (Component Diagram)

```mermaid
graph TB
    subgraph "طبقة العرض (Presentation Layer)"
        UI["واجهات الويب (Jinja2 HTML / CSS3 / Vanilla JS)"]
        ChatUI["مكون الشات اللحظي (AJAX Polling Engine)"]
    end

    subgraph "طبقة منطق الأعمال (Application Logic Layer)"
        FlaskCore["محرك التطبيق المركزي (Flask app.py)"]
        AuthModule["وحدة الصلاحيات والمصادقة (RBAC & Auth)"]
        FaultModule["وحدة إدارة الأعطال والجدولة (Fault Management)"]
        ReportModule["محرك التقارير (PDF & Excel Exports)"]
        SecurityModule["طبقة الأمان (Bcrypt, CSRF, Secure Upload)"]
    end

    subgraph "طبقة البيانات (Data Layer)"
        PostgresDB[("قاعدة البيانات PostgreSQL / MySQL")]
        FileStorage[("مجلد المرفقات (Uploads)")]
        MailServer[("خادم البريد SMTP")]
    end

    UI --> FlaskCore
    ChatUI --> FlaskCore
    FlaskCore --> SecurityModule
    FlaskCore --> AuthModule
    FlaskCore --> FaultModule
    FlaskCore --> ReportModule
    
    AuthModule --> PostgresDB
    FaultModule --> PostgresDB
    FaultModule --> FileStorage
    FaultModule --> MailServer
```

---

## 10. مخطط النشر والتوزيع (Deployment Diagram)

```mermaid
graph TB
    subgraph "أجهزة المستخدمين (Clients)"
        Desktop["متصفح الحاسوب المكتبي"]
        Mobile["متصفح الهاتف الذكي"]
    end

    subgraph "خادم الويب والتطبيق (Application Server)"
        Gunicorn["Gunicorn / WSGI Web Server"]
        FlaskEnv["بيئة تشغيل Python 3.10+ / Flask"]
        StaticFolder["الملفات الثابتة والمرفقات"]
    end

    subgraph "الخدمات السحابية الخارجية (Cloud Services)"
        SupabaseDB[("قاعدة بيانات PostgreSQL السحابية (Supabase)")]
        SMTPRelay[("خادم إرسال البريد (Google SMTP)")]
    end

    Desktop -->|HTTPS / TLS| Gunicorn
    Mobile -->|HTTPS / TLS| Gunicorn
    Gunicorn --> FlaskEnv
    FlaskEnv --> StaticFolder
    FlaskEnv -->|SSL Port 5432| SupabaseDB
    FlaskEnv -->|TLS Port 587| SMTPRelay
```

---
> 💡 **ملاحظة:** تتوفر أيضاً نسخة ويب تفاعلية متكاملة مع دعم المعاينة الحية والطباعة في المسار: [`docs/SYSTEM_ANALYSIS_AND_UML_DESIGN.html`](file:///c:/xampp/htdocs/it_fault_system/docs/SYSTEM_ANALYSIS_AND_UML_DESIGN.html) والوثيقة الشاملة المفصلة في [`docs/SYSTEM_ANALYSIS_AND_UML_DESIGN.md`](file:///c:/xampp/htdocs/it_fault_system/docs/SYSTEM_ANALYSIS_AND_UML_DESIGN.md).
