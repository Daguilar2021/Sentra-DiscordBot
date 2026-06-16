import { Routes } from '@angular/router';
import { Home } from './pages/home/home';
import { Documentation } from './pages/documentation/documentation';
import { Legal } from './pages/Legal/legal';
import { AuthSuccess } from './pages/auth/auth-success';

export const routes: Routes = [
    { path: '', component: Home },
    { path: 'documentation', component: Documentation },
    { path: 'legal', component: Legal },
    { path: 'auth/success', component: AuthSuccess }
];
