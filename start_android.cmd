@echo off
setlocal EnableExtensions

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

for /d %%J in ("C:\Program Files\Microsoft\jdk-17*") do set "JAVA_HOME=%%~fJ"
if not exist "%JAVA_HOME%\bin\java.exe" (
  echo [NOVA] JDK 17 was not found. Install Microsoft OpenJDK 17 first.
  pause
  exit /b 1
)

if not defined ANDROID_HOME set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
set "ADB=%ANDROID_HOME%\platform-tools\adb.exe"
set "EMULATOR=%ANDROID_HOME%\emulator\emulator.exe"
set "STUDIO=%LOCALAPPDATA%\Programs\AndroidStudioQuail3\android-studio\bin\studio64.exe"
if not exist "%STUDIO%" set "STUDIO=C:\Program Files\Android\Android Studio\bin\studio64.exe"
set "STUDIO_PROPERTIES=%PROJECT_ROOT%\scripts\android-studio.properties"
set "PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator;%ANDROID_HOME%\cmdline-tools\latest\bin;%PATH%"
set "ORG_GRADLE_PROJECT_kotlin.compiler.execution.strategy=in-process"
set "ORG_GRADLE_PROJECT_org.gradle.jvmargs=-Xmx3072m -XX:MaxMetaspaceSize=1024m"

if not exist "%ADB%" (
  echo [NOVA] Android SDK platform-tools were not found at %ANDROID_HOME%.
  pause
  exit /b 1
)

netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul 2>&1
if errorlevel 1 start "NOVA Django API" cmd.exe /k call "%PROJECT_ROOT%\scripts\start_backend_android.cmd"

set "NOVA_DEVICE="
for /f "tokens=1" %%D in ('adb.exe devices ^| findstr /b "emulator-" ^| findstr "device"') do set "NOVA_DEVICE=%%D"
if not defined NOVA_DEVICE (
  "%EMULATOR%" -list-avds | findstr /x /c:"NOVA_API_36" >nul
  if errorlevel 1 (
    echo [NOVA] The NOVA_API_36 emulator was not found in Android Studio.
    pause
    exit /b 1
  )
  start "NOVA Android Emulator" "%EMULATOR%" -avd NOVA_API_36 -netdelay none -netspeed full
)

set /a WAIT_COUNT=0
:wait_for_device
set "NOVA_DEVICE="
for /f "tokens=1" %%D in ('adb.exe devices ^| findstr /b "emulator-" ^| findstr "device"') do set "NOVA_DEVICE=%%D"
if defined NOVA_DEVICE goto wait_for_boot
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GEQ 120 (
  echo [NOVA] Android emulator did not connect in time.
  pause
  exit /b 1
)
timeout /t 2 /nobreak >nul
goto wait_for_device

:wait_for_boot
set "BOOT_STATUS="
for /f "delims=" %%B in ('adb.exe -s "%NOVA_DEVICE%" shell getprop sys.boot_completed 2^>nul') do set "BOOT_STATUS=%%B"
if not "%BOOT_STATUS%"=="1" (
  timeout /t 3 /nobreak >nul
  goto wait_for_boot
)
set "ANDROID_SERIAL=%NOVA_DEVICE%"

cd /d "%PROJECT_ROOT%\apps\mobile"
call npm.cmd install || exit /b 1
if not exist "android\gradlew.bat" (
  call npx.cmd expo prebuild --platform android || exit /b 1
)

if exist "%STUDIO%" start "NOVA Android Studio" "%STUDIO%" "%PROJECT_ROOT%\apps\mobile\android"

call npx.cmd expo run:android
