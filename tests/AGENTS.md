# BookForge Testing Subsystem Developer Instructions

Use these rules when writing unit tests, integration tests, or regression assertions under the `tests/` directory.

---

## 1. Test Architecture & Conventions
- **Naming**: Test files must be named `test_*.py`. Individual test classes must inherit from `unittest.TestCase`.
- **Coverage**: Every new core feature or bug fix must have a corresponding test case verifying its behavior.
- **Execution**: Run the full test suite using standard discovery:
  ```bash
  python3 -m unittest discover tests/
  ```

---

## 2. Sandbox Isolation & Permissions
- **Zero Monolithic /tmp Pollution**: Do not write test artifacts directly to the global `/tmp` directory. Some execution sandboxes restrict permissions there, causing clean-up errors.
- **Local Scratch Directory**: Use local, isolated workspace directories (e.g. `scratch_test_temp/`) for test-induced file creations.
- **Cleanup**: Always register automatic directory removal in `setUp()` and `tearDown()` hooks:
  ```python
  def setUp(self):
      self.test_dir = Path("scratch_test_temp")
      self.test_dir.mkdir(exist_ok=True)

  def tearDown(self):
      if self.test_dir.exists():
          shutil.rmtree(self.test_dir)
  ```

---

## 3. Mocking & Dependencies
- Mock external network APIs (such as NotebookLM) using `unittest.mock.patch`.
- Use mock filesystems or mock file pointers where appropriate to test scanners and parsers without writing physical files.
