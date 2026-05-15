import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_root_department(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Engineering"})
    assert r.status_code == 201
    
    data = r.json()
    
    assert data["name"] == "Engineering"
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_create_child_department(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Root A"})
    parent_id = r.json()["id"]

    r = await client.post("/api/v1/departments/", json={"name": "Backend", "parent_id": parent_id})
    
    assert r.status_code == 201
    assert r.json()["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_duplicate_name_same_parent_returns_409(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Root B"})
    parent_id = r.json()["id"]

    await client.post("/api/v1/departments/", json={"name": "Team X", "parent_id": parent_id})
    
    r2 = await client.post("/api/v1/departments/", json={"name": "Team X", "parent_id": parent_id})
    
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_name_trimmed(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "  Trimmed  "})
    
    assert r.status_code == 201
    assert r.json()["name"] == "Trimmed"


@pytest.mark.asyncio
async def test_empty_name_returns_422(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_department_nonexistent_parent(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Orphan", "parent_id": 99999})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_department_detail_with_employees(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Dept Detail"})
    dept_id = r.json()["id"]

    await client.post(
        f"/api/v1/departments/{dept_id}/employees/",
        json={"full_name": "Роман Иванов", "position": "Разработчик"},
    )

    r = await client.get(f"/api/v1/departments/{dept_id}")
    assert r.status_code == 200
    data = r.json()
    
    assert data["id"] == dept_id
    assert len(data["employees"]) == 1
    assert data["employees"][0]["full_name"] == "Роман Иванов"
    assert data["employees"][0]["position"] == "Разработчик"


@pytest.mark.asyncio
async def test_get_department_depth(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Grandparent"})
    gp_id = r.json()["id"]

    r = await client.post("/api/v1/departments/", json={"name": "Parent", "parent_id": gp_id})
    p_id = r.json()["id"]

    await client.post("/api/v1/departments/", json={"name": "Child", "parent_id": p_id})

    # depth=1 → only direct children
    r = await client.get(f"/api/v1/departments/{gp_id}?depth=1")
    data = r.json()

    assert len(data["children"]) == 1
    assert data["children"][0]["children"] == []

    # depth=2 → two levels
    r = await client.get(f"/api/v1/departments/{gp_id}?depth=2")
    data = r.json()

    assert len(data["children"][0]["children"]) == 1


@pytest.mark.asyncio
async def test_update_department_name(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Старое имя"})
    dept_id = r.json()["id"]

    r = await client.patch(f"/api/v1/departments/{dept_id}", json={"name": "Новое имя"})

    assert r.status_code == 200
    assert r.json()["name"] == "Новое имя"


@pytest.mark.asyncio
async def test_move_department_cycle_returns_409(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Cycle Parent"})
    p_id = r.json()["id"]

    r = await client.post("/api/v1/departments/", json={"name": "Cycle Child", "parent_id": p_id})
    c_id = r.json()["id"]

    r = await client.patch(f"/api/v1/departments/{p_id}", json={"parent_id": c_id})
    
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_self_parent_returns_409(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Self Loop"})
    dept_id = r.json()["id"]

    r = await client.patch(f"/api/v1/departments/{dept_id}", json={"parent_id": dept_id})
    
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_delete_cascade(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "To Cascade"})
    dept_id = r.json()["id"]

    await client.post(f"/api/v1/departments/{dept_id}/employees/", json={"full_name": "Роман Иванов", "position": "Разработчик"})

    r = await client.delete(f"/api/v1/departments/{dept_id}?mode=cascade")
    assert r.status_code == 204

    r = await client.get(f"/api/v1/departments/{dept_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_reassign(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Source Dept"})
    src_id = r.json()["id"]

    r = await client.post("/api/v1/departments/", json={"name": "Target Dept"})
    tgt_id = r.json()["id"]

    r = await client.post(f"/api/v1/departments/{src_id}/employees/", json={"full_name": "Роман Иванов", "position": "Разработчик"})
    emp_id = r.json()["id"]

    r = await client.delete(f"/api/v1/departments/{src_id}?mode=reassign&reassign_to_department_id={tgt_id}")

    assert r.status_code == 204
    
    # Сейчас работник должен быть в целевом отделе
    r = await client.get(f"/api/v1/departments/{tgt_id}")

    assert any(e["id"] == emp_id for e in r.json()["employees"])


@pytest.mark.asyncio
async def test_delete_reassign_missing_target_returns_422(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "No Target"})
    dept_id = r.json()["id"]

    r = await client.delete(f"/api/v1/departments/{dept_id}?mode=reassign")
    
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_employee_nonexistent_department(client: AsyncClient):
    r = await client.post("/api/v1/departments/99999/employees/", json={"full_name": "Ghost", "position": "None"})

    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_employee_empty_full_name_returns_422(client: AsyncClient):
    r = await client.post("/api/v1/departments/", json={"name": "Valid Dept"})
    dept_id = r.json()["id"]

    r = await client.post(f"/api/v1/departments/{dept_id}/employees/", json={"full_name": "", "position": "Dev"})
    
    assert r.status_code == 422