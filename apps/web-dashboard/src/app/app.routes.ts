import { Routes } from '@angular/router';
import { Home } from './pages/home/home';
import { Documentation } from './pages/documentation/documentation';
import { AuthSuccess } from './pages/auth-success/auth-success';

export const routes: Routes = [
    { path: '', component: Home },
    { path: 'documentation', component: Documentation },
    { path: 'auth/success', component: AuthSuccess }
];
