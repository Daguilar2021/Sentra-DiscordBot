import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';


@Injectable({
  providedIn: 'root'
})
export class DiscordService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiBaseUrl}/api/invite`;

  getInviteUrl(): Observable<string> {
    return this.http.get<{ url: string }>(this.apiUrl).pipe(
      map(response => response.url)
    );
  }
}
