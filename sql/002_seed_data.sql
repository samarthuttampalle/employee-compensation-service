SET IDENTITY_INSERT dbo.Department ON;
INSERT INTO dbo.Department (DepartmentID, DepartmentName, Location)
VALUES
    (1, 'Engineering', 'Bengaluru'),
    (2, 'HR', 'Hyderabad'),
    (3, 'Finance', 'Mumbai'),
    (4, 'Operations', 'Pune'),
    (5, 'Legal', 'Chennai');
SET IDENTITY_INSERT dbo.Department OFF;
GO

SET IDENTITY_INSERT dbo.Employee ON;
INSERT INTO dbo.Employee (
    EmployeeID, FirstName, LastName, DepartmentID, Salary, Bonus, HireDate
)
VALUES
    (1, 'Aarav', 'Sharma', 1, 120000.00, 10000.00, '2022-01-10'),
    (2, 'Diya', 'Patel', 1, 115000.00, NULL, '2022-03-18'),
    (3, 'Neha', 'Iyer', 2, 75000.00, 5000.00, '2021-09-01'),
    (4, 'Rohan', 'Verma', 2, 73000.00, NULL, '2023-02-14'),
    (5, 'Karan', 'Mehta', 3, 100000.00, 25000.00, '2020-07-07'),
    (6, 'Mira', 'Nair', 3, 88000.00, 15000.00, '2021-11-22'),
    (7, 'Priya', 'Rao', 4, 98000.00, 15000.00, '2020-05-30'),
    (8, 'Ishan', 'Kapoor', NULL, 60000.00, NULL, '2024-01-05'),
    (9, 'Sana', 'Khan', 1, 200000.00, 2000.00, '2019-08-19'),
    (10, 'Vikram', 'Das', 3, 150000.00, 30000.00, '2018-04-12');
SET IDENTITY_INSERT dbo.Employee OFF;
GO
