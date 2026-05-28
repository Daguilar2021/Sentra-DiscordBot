import { Component } from '@angular/core';
import { ActivatedRoute, Router, } from '@angular/router';
import { OnInit , inject} from '@angular/core';

@Component({
  selector: 'app-auth-success',
  templateUrl: './auth-success.html',
  styleUrl: './auth-success.css',
})
export class AuthSuccess implements OnInit {

  private route = inject(ActivatedRoute);
  private router = inject(Router);

  ngOnInit(): void {
    const code = this.route.snapshot.queryParamMap.get('code');
    const state = this.route.snapshot.queryParamMap.get('state');

    // Missing OAuth parameters
    if (!code || !state) {
      this.router.navigate(['/']);
      return;
    }

  }

}
