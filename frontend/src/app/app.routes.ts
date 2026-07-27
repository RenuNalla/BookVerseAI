import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

/**
 * Lazy-loaded feature routes. Each feature is a standalone component
 * loaded on demand, so the initial bundle only contains the shell +
 * whichever page the user lands on. New phases add one entry each:
 * /login, /register (Phase 2), /reader/:id (Phase 7), /audiobook/:id
 * (Phase 8), etc.
 */
export const routes: Routes = [
  {
    path: '',
    redirectTo: 'upload',
    pathMatch: 'full',
  },
  {
    path: 'upload',
    loadComponent: () =>
      import('./features/upload/upload.component').then(
        (m) => m.UploadComponent
      ),
    title: 'Translate a Book',
  },
  {
    path: 'library',
    loadComponent: () =>
      import('./features/library/library.component').then(
        (m) => m.LibraryComponent
      ),
    title: 'My Library',
    canActivate: [authGuard],
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then(
        (m) => m.LoginComponent
      ),
    title: 'Log In',
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/register/register.component').then(
        (m) => m.RegisterComponent
      ),
    title: 'Sign Up',
  },
  {
    path: '**',
    redirectTo: 'upload',
  },
];