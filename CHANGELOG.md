

# 6.2.0

* **Changed:** Dependencies have been upgraded and newer django versions have been added 
* **CI:** Travis CI has been replaced by GitHub Actions

# 6.1.3

* **Added** ip is now record (fixes #12)
* **Fix:** #9 and #11. Previously we would try to register everytime it was initialized, which would break admin (which
  does an isinstance check). The decorator now registers on a module - not thread - level. The hidden `__dal_register__`
  method is now attached, which will re-register if needed.

# 6.1.2

> Release was an error, did not do anything
