#!/usr/bin/env python3
"""
Скрипт для создания PDF с таблицей для тестирования.
"""

from pathlib import Path


def create_table_pdf():
    """Создает простой PDF с таблицей для тестирования."""

    # Создаем директорию если не существует
    fixtures_dir = Path("tests/fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # Создаем простой HTML с таблицей и конвертируем в PDF
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Employee Data</title>
    <style>
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>Employee Database</h1>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Department</th>
                <th>Salary</th>
                <th>Experience</th>
                <th>Location</th>
                <th>Skills</th>
                <th>Rating</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>1</td><td>John Smith</td><td>Engineering</td><td>$85,000</td><td>5 years</td><td>New York</td><td>Python, JavaScript, SQL</td><td>4.5</td></tr>
            <tr><td>2</td><td>Sarah Johnson</td><td>Sales</td><td>$75,000</td><td>3 years</td><td>San Francisco</td><td>CRM, Negotiation</td><td>4.2</td></tr>
            <tr><td>3</td><td>Mike Davis</td><td>Marketing</td><td>$70,000</td><td>4 years</td><td>London</td><td>SEO, Analytics</td><td>4.0</td></tr>
            <tr><td>4</td><td>Lisa Wilson</td><td>HR</td><td>$65,000</td><td>6 years</td><td>Berlin</td><td>Recruitment, HRIS</td><td>4.3</td></tr>
            <tr><td>5</td><td>David Brown</td><td>Finance</td><td>$90,000</td><td>8 years</td><td>Tokyo</td><td>Excel, SAP</td><td>4.7</td></tr>
            <tr><td>6</td><td>Emma Taylor</td><td>Operations</td><td>$80,000</td><td>7 years</td><td>Sydney</td><td>Project Management</td><td>4.4</td></tr>
            <tr><td>7</td><td>James Anderson</td><td>Engineering</td><td>$95,000</td><td>9 years</td><td>New York</td><td>Java, Spring, AWS</td><td>4.8</td></tr>
            <tr><td>8</td><td>Maria Garcia</td><td>Sales</td><td>$78,000</td><td>4 years</td><td>San Francisco</td><td>B2B Sales, CRM</td><td>4.1</td></tr>
            <tr><td>9</td><td>Robert Martinez</td><td>Marketing</td><td>$72,000</td><td>5 years</td><td>London</td><td>Social Media, PPC</td><td>4.2</td></tr>
            <tr><td>10</td><td>Jennifer Lee</td><td>HR</td><td>$68,000</td><td>5 years</td><td>Berlin</td><td>Benefits, Compliance</td><td>4.5</td></tr>
        </tbody>
    </table>
</body>
</html>
"""

    # Сохраняем HTML
    html_path = fixtures_dir / "table.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Пытаемся конвертировать в PDF используя wkhtmltopdf или другой инструмент
    pdf_path = fixtures_dir / "table.pdf"

    # Если wkhtmltopdf доступен
    try:
        import subprocess

        result = subprocess.run(
            [
                "wkhtmltopdf",
                "--page-size",
                "A4",
                "--margin-top",
                "10mm",
                "--margin-bottom",
                "10mm",
                "--margin-left",
                "10mm",
                "--margin-right",
                "10mm",
                str(html_path),
                str(pdf_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Created tests/fixtures/table.pdf using wkhtmltopdf")
            return
        else:
            print(f"⚠️ wkhtmltopdf failed: {result.stderr}")
    except (FileNotFoundError, ImportError):
        print("⚠️ wkhtmltopdf not available")

    # Fallback: создаем простой текстовый файл с таблицей
    table_content = """Employee Database

ID | Name | Department | Salary | Experience | Location | Skills | Rating
---|------|------------|--------|------------|----------|--------|-------
1 | John Smith | Engineering | $85,000 | 5 years | New York | Python, JavaScript, SQL | 4.5
2 | Sarah Johnson | Sales | $75,000 | 3 years | San Francisco | CRM, Negotiation | 4.2
3 | Mike Davis | Marketing | $70,000 | 4 years | London | SEO, Analytics | 4.0
4 | Lisa Wilson | HR | $65,000 | 6 years | Berlin | Recruitment, HRIS | 4.3
5 | David Brown | Finance | $90,000 | 8 years | Tokyo | Excel, SAP | 4.7
6 | Emma Taylor | Operations | $80,000 | 7 years | Sydney | Project Management | 4.4
7 | James Anderson | Engineering | $95,000 | 9 years | New York | Java, Spring, AWS | 4.8
8 | Maria Garcia | Sales | $78,000 | 4 years | San Francisco | B2B Sales, CRM | 4.1
9 | Robert Martinez | Marketing | $72,000 | 5 years | London | Social Media, PPC | 4.2
10 | Jennifer Lee | HR | $68,000 | 5 years | Berlin | Benefits, Compliance | 4.5
"""

    # Сохраняем как текстовый файл (для тестирования парсинга)
    txt_path = fixtures_dir / "table.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(table_content)

    print("✅ Created tests/fixtures/table.txt (fallback)")
    print("⚠️ Please install wkhtmltopdf for PDF generation or use existing PDF")


if __name__ == "__main__":
    create_table_pdf()
