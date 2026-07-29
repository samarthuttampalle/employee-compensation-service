/*
Phase 1 - Schema teardown script
*/

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
