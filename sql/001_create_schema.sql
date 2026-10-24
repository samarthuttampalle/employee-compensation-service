IF OBJECT_ID('dbo.Employee', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Employee;
END;
GO

IF OBJECT_ID('dbo.Department', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Department;
END;
GO

CREATE TABLE dbo.Department (
    DepartmentID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    DepartmentName VARCHAR(100) NOT NULL,
    Location VARCHAR(100) NULL,
    CONSTRAINT UQ_Department_DepartmentName UNIQUE (DepartmentName)
);
GO

CREATE TABLE dbo.Employee (
    EmployeeID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    DepartmentID INT NULL,
    Salary DECIMAL(12,2) NOT NULL,
    Bonus DECIMAL(12,2) NULL,
    HireDate DATE NULL,
    CONSTRAINT CK_Employee_Salary_Positive CHECK (Salary > 0),
    CONSTRAINT CK_Employee_Bonus_NonNegative CHECK (Bonus IS NULL OR Bonus >= 0),
    CONSTRAINT FK_Employee_Department
        FOREIGN KEY (DepartmentID)
        REFERENCES dbo.Department(DepartmentID)
        ON DELETE SET NULL
);
GO

CREATE INDEX IX_Employee_DepartmentID ON dbo.Employee (DepartmentID);
GO

CREATE INDEX IX_Employee_Bonus ON dbo.Employee (Bonus) INCLUDE (Salary);
GO
