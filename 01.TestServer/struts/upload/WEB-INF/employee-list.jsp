<%@ page contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="s" uri="/struts-tags" %>
<html>
<head>
    <title>직원 목록</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --card: #ffffff;
            --text: #1f2a44;
            --muted: #6b7280;
            --accent: #3b82f6;
            --accent-strong: #1d4ed8;
            --border: #e5e7eb;
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: "Segoe UI", "Noto Sans KR", sans-serif;
            background: var(--bg);
            color: var(--text);
        }

        .page {
            max-width: 1100px;
            margin: 0 auto;
            padding: 48px 24px 80px;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            margin-bottom: 32px;
        }

        .title h1 {
            margin: 0 0 8px;
            font-size: 28px;
            font-weight: 700;
        }

        .title p {
            margin: 0;
            color: var(--muted);
        }

        .actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 10px 16px;
            border-radius: 12px;
            font-weight: 600;
            text-decoration: none;
        }

        .btn.secondary {
            background: #e0e7ff;
            color: #3730a3;
        }

        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }

        .search {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 16px;
        }

        .search input {
            flex: 1;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 10px 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            text-align: left;
            padding: 10px 8px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }

        th {
            font-weight: 600;
            color: var(--muted);
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            background: #eef2ff;
            color: #4338ca;
        }

        .avatar {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            object-fit: cover;
            border: 1px solid var(--border);
            background: #fff;
        }

        .avatar.placeholder {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #e0e7ff;
            color: #3730a3;
            font-weight: 700;
        }
    </style>
</head>
<body>
<div class="page">
    <header>
        <div class="title">
            <h1>직원 목록</h1>
            <p>등록된 직원 정보를 확인하세요.</p>
        </div>
        <div class="actions">
            <s:url var="listUrl" action="employees" />
            <s:url var="createUrl" action="employee-create" />
            <a class="btn secondary" href="<s:property value='#listUrl' />">직원 목록</a>
            <a class="btn" href="<s:property value='#createUrl' />">직원 등록</a>
        </div>
    </header>

    <section class="card">
        <div class="search">
            <input id="employeeSearch" type="text" placeholder="이름, 부서, 직무로 검색" onkeyup="filterEmployees()" />
        </div>
        <table id="employeeTable">
            <thead>
                <tr>
                    <th>사진</th>
                    <th>사번</th>
                    <th>이름</th>
                    <th>부서</th>
                    <th>직무</th>
                    <th>상태</th>
                </tr>
            </thead>
            <tbody>
                <s:iterator value="employees">
                    <tr>
                        <td>
                            <s:if test="imageFileName != null && !imageFileName.isEmpty()">
                                  <img class="avatar"
                                      src="${pageContext.request.contextPath}/uploads/faces/<s:property value='imageFileName' />"
                                      alt="직원 사진" />
                            </s:if>
                            <s:else>
                                <div class="avatar placeholder">
                                    <s:property value="name.substring(0,1)" />
                                </div>
                            </s:else>
                        </td>
                        <td><s:property value="employeeCode"/></td>
                        <td><s:property value="name"/></td>
                        <td><s:property value="department"/></td>
                        <td><s:property value="role"/></td>
                        <td><span class="status"><s:property value="status"/></span></td>
                    </tr>
                </s:iterator>
            </tbody>
        </table>
    </section>
</div>

<script>
    function filterEmployees() {
        const keyword = document.getElementById("employeeSearch").value.toLowerCase();
        const rows = document.querySelectorAll("#employeeTable tbody tr");
        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(keyword) ? "" : "none";
        });
    }
</script>
</body>
</html>
