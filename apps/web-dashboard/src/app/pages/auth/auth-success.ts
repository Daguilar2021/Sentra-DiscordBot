import { ActivatedRoute, Router, } from '@angular/router';
import {Component, OnInit , inject} from '@angular/core';

@Component({
  selector: 'app-auth-success',
  templateUrl: './auth-success.html',
  styleUrl: './auth-success.css',
})

export class AuthSuccess implements OnInit {

  private route = inject(ActivatedRoute);
  private router = inject(Router);

  isLoading = false;
  issuccess = false;
  errorMessage: string | null = '';
  discordId: string | null = '';
  guildId: string | null = '';
  email: string | null = '';

  ngOnInit(): void {
    // Get auth data from query params (redirected from backend)
    this.discordId = this.route.snapshot.queryParamMap.get('discordId');
    this.guildId = this.route.snapshot.queryParamMap.get('guildId');
    this.email = this.route.snapshot.queryParamMap.get('email');
    const error = this.route.snapshot.queryParamMap.get('error');

    if (error) {
      this.issuccess = false;
      this.errorMessage = `Authentication failed: ${error}`;
      return;
    }

    if (!this.discordId || !this.guildId) {
      this.issuccess = false;
      this.errorMessage = 'Missing authentication data';
      return;
    }

    this.issuccess = true;
  }

}
