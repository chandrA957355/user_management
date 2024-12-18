# User Management System 🚀  
### A Comprehensive Project for User Management with Bug Fixes, Enhancements, and Testing  

## 📚 **Project Overview**  
The **User Management System** is a robust and feature-rich application designed to manage user operations seamlessly. This project includes enhancements, bug fixes, testing improvements, and deployment configurations using Docker.

---

## ✨ **Project Features**  
| **Feature**                          | **Description**                                                                 |
|--------------------------------------|-------------------------------------------------------------------------------|
| **User Search and Filtering**        | Allows admins to search and filter users based on attributes like name/email. |
| **Secure Password Validation**       | Enforces strong password rules for enhanced security.                        |
| **Email/Token Validation Fixes**     | Fixes issues related to email verification and token validation.             |
| **Docker Build Configuration**       | Resolves Docker build issues for seamless deployment.                        |
| **Dependency Vulnerabilities Fixes** | Updates project dependencies to resolve high and critical vulnerabilities.   |

---

## 🚰 **Setup Instructions**  

Follow these steps to set up the project locally:  

### **1. Prerequisites**  
- Python 3.10+  
- Docker and Docker Compose  
- PostgreSQL  

### **2. Installation**  

1. Clone the repository:  
   ```bash
   git clone https://github.com/chandrA957355/user_management.git
   cd user_management
   ```

2. Build and start the Docker containers:
   ```bash
   docker-compose up --build -d
   ```

3. Access the FastAPI Swagger UI at:
   ```arduino
   http://localhost/docs
   ```

---

## 🔍 **Bug Fixes and Enhancements**  

### 1. Bug Fixes  
| **Bug ID** | **Description**                                                            | **Solution**                                                                        | **Link**     |
|------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------|--------------|
| **#13**    | `verify_email_with_token` method did not check if the user was already verified. | Added a check to validate the token before marking the email as verified.          | [Issue #13](https://github.com/chandrA957355/user_management/issues/13) |
| **#11**    | Email/Nickname uniqueness validation blocks the user self-update.         | Added backend validation to ensure uniqueness only during conflicting updates.     | [Issue #11](https://github.com/chandrA957355/user_management/issues/11) |
| **#7**     | Duplicate email or nickname allowed during user update.                  | Introduced database constraints and validation checks at the service layer.        | [Issue #7](https://github.com/chandrA957355/user_management/issues/7)  |
| **#5**     | Passwords were not validated for security strength.                      | Enforced rules requiring uppercase, lowercase, numbers, and special characters.    | [Issue #5](https://github.com/chandrA957355/user_management/issues/5)  |
| **#3**     | Critical vulnerabilities were detected in project dependencies.          | Upgraded dependencies to secure versions using `pip audit` and dependency updates. | [Issue #3](https://github.com/chandrA957355/user_management/issues/3)  |
| **#1**     | Docker build failed due to libc-bin installation conflicts.              | Resolved Dockerfile issues by adjusting configurations for libc-bin installation.  | [Issue #1](https://github.com/chandrA957355/user_management/issues/1)  |

### 2. Enhancements  
| **Enhancement ID** | **Feature**                  | **Description**                                                        | **Link**     |
|---------------------|-----------------------------|------------------------------------------------------------------------|--------------|
| **#15**             | User Search and Filtering  | Added support for admins to search and filter users using attributes.  | [Issue #15](https://github.com/chandrA957355/user_management/issues/15) |

---

## ✅ **Testing**  

### Test Cases Added:
- **Duplicate Email Validation**: Tests to ensure that duplicate emails or nicknames cannot be used.
- **Password Validation**: Verifies strong passwords.
- **Token Verification**: Ensures tokens do not overwrite existing roles.
- **Search and Filter**: Tests the efficiency of user search and filtering functionality.

### Command to Run Tests  
To execute the test suite, run:  
```bash
docker compose exec fastapi pytest tests/
```

---

## 🚢 **Deployment**  

The project is containerized with Docker. To deploy:

1. Build the containers:
   ```bash
   docker-compose up --build -d
   ```

2. Access the project at:
   ```arduino
   http://localhost
   ```

---

## 🎯 **Project Goals Achieved**  
| **Objective**       | **Achievement**                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| **Fix Bugs**        | Resolved multiple issues for email verification, password validation, etc.   |
| **Feature Enhancement** | Added advanced search and filtering for user management.                   |
| **Test Coverage**   | Added unit tests for improved reliability.                                   |
| **Deployment**      | Fixed Docker build issues for successful deployment.                        |

---

## 🚀 **Key Links**  
- **GitHub Repository**: [User Management System](https://github.com/chandrA957355/user_management)
- **Closed Issues**:
  - [Issue #13](https://github.com/chandrA957355/user_management/issues/13)
  - [Issue #11](https://github.com/chandrA957355/user_management/issues/11)
  - [Issue #9](https://github.com/chandrA957355/user_management/issues/9)
  - [Issue #7](https://github.com/chandrA957355/user_management/issues/7)
  - [Issue #5](https://github.com/chandrA957355/user_management/issues/5)
  - [Issue #3](https://github.com/chandrA957355/user_management/issues/3)
- **DockerHub**: [DockerHub Link](https://hub.docker.com/repository/docker/chandra957355/user_management/general)

---

## 🏆 **Reflection**  
This project allowed me to resolve real-world issues, add critical features, and ensure the reliability of the user management system. By fixing bugs, adding validations, and enhancing functionalities, I strengthened my problem-solving, testing, and deployment skills.

---

## 👨‍💻 **Contributor**  
- **Name**: [chandrA957355]  
- **GitHub Profile**: [GitHub Link](https://github.com/chandrA957355)
