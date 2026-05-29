# Bolao Copa 2026 Android

Wrapper Android com Capacitor para publicar o Bolao Copa 2026 usando o mesmo backend web:

`https://bolao2026-9jgh.onrender.com`

## Desenvolvimento local

```powershell
cd "C:\Users\Wilber Kohler\Documents\Python\Bolao 2\mobile\android-wrapper"
npm install
npm run android:prepare
```

Para abrir no Android Studio:

```powershell
npm run android:open
```

## Build em nuvem

Use o workflow do GitHub Actions `Android Capacitor Build`.

O primeiro build gera um APK debug para teste. Para publicar na Play Store, gere um AAB release assinado com uma keystore propria.
